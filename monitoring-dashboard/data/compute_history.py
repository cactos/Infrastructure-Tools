import happybase 
import logging
from datetime import datetime
from app import cfg
import data.compute_cn as computeCN
import re
from multiprocessing import Process, Manager

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

host = cfg['servers']['thrift']
port = cfg['servers']['thriftport']

timebuckets = 60

def timesorter(a, b):
    if abs(a['start']-a['end']) > abs(b['start']-b['end']):
        return 1
    if abs(a['start']-a['end']) == abs(b['start']-b['end']):
        return 0
    else:
        return -1

def requestHistoryForNodes(computenodelist, start, end):
	starttime = datetime.now()
	processes = []
	#result = {}
	manager = Manager()
	result = manager.dict()
	
	for computenode in computenodelist:
		p = Process(target=requestHistoryForSingleNode, args=(computenode, start, end, result))
		processes.append(p)
		p.start()

	for process in processes:
		process.join()

	# merge VMs from computenode to total list
	vmslist = {}
	vmsWithOverlap = {}
	for computenode in computenodelist:
		for vmid in result[computenode]['vms']['list']:
			vmtimes = result[computenode]['vms']['list'][vmid]
			if not vmid in vmslist:
				vmslist.update({vmid: vmtimes})
				continue

			# check if time ranges overlap
			if (vmslist[vmid][0] <= vmtimes[0] and vmslist[vmid][1] >= vmtimes[1]) or (vmtimes[0] <= vmslist[vmid][0] and vmtimes[1] >= vmslist[vmid][1]):
				# overlap detected
				logging.info('overlap detected for vm %s' % vmid)
				vmsWithOverlap.update({ vmid: vmtimes })
				
			# extend time ranges
			if vmtimes[0] < vmslist[vmid][0]:
				vmslist[vmid][0] =  vmtimes[0]
			if vmtimes[1] > vmslist[vmid][1]:
				vmslist[vmid][1] =  vmtimes[1]
	result.update({ 'vmslist' : vmslist })
	
	# get rid of strange manager references ...
	result = result.copy()	
	# solve overlapping VMs in computenodes	
	for vmid in vmsWithOverlap:
		conflictingTime = vmsWithOverlap[vmid]
		affectedNodes = []
		for computenode in computenodelist:
			if not vmid in result[computenode]['vms']['list']:
				continue
			affectedNodes.append({'node': computenode, 'start': result[computenode]['vms']['list'][vmid][0], 'end': result[computenode]['vms']['list'][vmid][1] })
		# sort nodes by vm life time 
		affectedNodes.sort(timesorter, reverse=True)
		for i in range(0,len(affectedNodes)):
			#cnvmdata = result[affectedNodes[i]['node']]['vms']['data']
			for j in range(i+1,len(affectedNodes)):
				if affectedNodes[i]['start'] <= affectedNodes[j]['start'] and affectedNodes[i]['end'] >= affectedNodes[j]['end']:
					logging.info('cut vm overlap from node %s (range %i:%i) - winning node %s (range %i:%i)' % (affectedNodes[i]['node'], affectedNodes[i]['start'], affectedNodes[i]['end'], affectedNodes[j]['node'], affectedNodes[j]['start'], affectedNodes[j]['end']))
					for k in range(affectedNodes[j]['start'], affectedNodes[j]['end']+1):
						result[affectedNodes[i]['node']]['vms']['data'][k] -= 1
	
	# calculate amount of VMs per time bucket
	vmscount = [0]*timebuckets
	for index in range(timebuckets):
		counter = 0
		for vmid in vmslist:
			vmtimes = vmslist[vmid]
			if vmtimes[0] <= index and vmtimes[1] >= index:
				counter += 1
		vmscount[index] = counter		
	result.update({ 'vmscount' : vmscount })
	
	endtime = datetime.now()
	logging.info('Finished requestHistoryForNodes in %s' % (endtime-starttime))
	
	return result.copy()

def requestHistoryForSingleNode(computenode, start, end, result):
	logging.info('Querying for computenode %s' % computenode)
	querytimestart = datetime.now()
	# run the query
	result[computenode] = requestHistory(computenode, start, end)
	querytimeend = datetime.now()
	logging.info('Computenode %s finished in %s' % (computenode, querytimeend-querytimestart))
	
def requestHistory(query_computenode, query_starttime, query_endtime):
	logging.info('New request history %s %s %s' % (query_computenode, query_starttime, query_endtime) )
	logging.info('Open connection pool to host %s:%s' % (host, port ))
	
	#query_computenode = 'computenode12'
	#query_starttime = '1476136800000'
	#query_endtime = '1476309600000'
	
	interval = int((int(query_endtime) - int(query_starttime)) / timebuckets)

	# define metrics we consider
	metrics = {
		'power': 'power_util:consumption',
		'cpu_sys': 'hardware_util:cpu_sys',
		'cpu_usr': 'hardware_util:cpu_usr',
		'cpu_wio': 'hardware_util:cpu_wio',
		'cpu_total': None,
		'mem_size': 'hardware:mem_size',
		'mem_free': 'hardware_util:mem_free',
		'mem_cache': 'hardware_util:mem_cache',
		'mem_used': None,
		'net_through': 'network_util:net_through',
		'vms': 'vms'
	}
	
	columns = filter(None, metrics.values()) # get columns for hbase
	
	# initialise result map for each metric
	result = { }
	for key in metrics:
		result[key] = [0]*timebuckets
	vmslist = {}
	
	pool = happybase.ConnectionPool(size=10, host=host, port=port)
	with pool.connection() as connection:

		logging.info('Open connection to table CNHistory')
		table = connection.table('CNHistory')
		logging.info('Connection to table established')
	
		logging.info('Scan from table')
		starttime = datetime.now()
		
		tmp_sums = {}
		for key in metrics:
			tmp_sums[key] = 0
		tmp_counts = {}
		for key in metrics:
			tmp_counts[key] = 0
		
		counter = 0
		index = 0
		row_start = query_computenode+'-'+query_starttime
		row_stop = query_computenode+'-'+query_endtime
		for key, data in table.scan(row_start=row_start, row_stop=row_stop, columns=columns, batch_size=1000):
			try:
				row_timestamp = int(key.replace(query_computenode+'-', ''))
			except:
				print "cannot parse row key %s " % key
				continue
			
			#logging.info('key %s %s' % (key, data))
			counter += 1
			
			# if we just crossed a time bucket border, group values and start on empty bucket for next time frame
			try: 
				if ((row_timestamp - int(query_starttime)) >= ((index + 1) * interval)):
					# calculate average
					for key in metrics:
						if tmp_counts[key] == 0:
							result[key][index] = 0
						else:
							result[key][index] = int(tmp_sums[key] / tmp_counts[key])
					# fill mem_size with previous value if not present
					if result['mem_size'][index] == 0 and index > 0:
						result['mem_size'][index] = result['mem_size'][index-1]
					# calculate mem_used from used=(size-free)
					result['mem_used'][index] = result['mem_size'][index] - result['mem_free'][index]
					if result['mem_used'][index] < 0:
						result['mem_used'][index] = 0
					 
					# reset caches
					tmp_sums = {}
					for key in metrics:
						tmp_sums[key] = 0
					tmp_counts = {}
					for key in metrics:
						tmp_counts[key] = 0

					# search next time bucket
					while ((index < timebuckets) and ((row_timestamp - int(query_starttime)) > ((index + 1) * interval))):
						index += 1
						# fix mem_size
						result['mem_size'][index] = result['mem_size'][index-1]
			except Exception as e:
				print "Exception while computing average"
				print e
				continue
			
			try: 
				# handle CPU if present
				if 'hardware_util:cpu_sys' in data:
					cpu_sys = getInt(data, 'hardware_util:cpu_sys')
					cpu_usr = getInt(data, 'hardware_util:cpu_usr')
					cpu_wio = getInt(data, 'hardware_util:cpu_wio')
					cpu_total =  cpu_sys + cpu_usr + cpu_wio
					tmp_sums['cpu_sys'] += cpu_sys
					tmp_counts['cpu_sys'] += 1
					tmp_sums['cpu_usr'] += cpu_usr
					tmp_counts['cpu_usr'] += 1
					tmp_sums['cpu_wio'] += cpu_wio
					tmp_counts['cpu_wio'] += 1
					tmp_sums['cpu_total'] += cpu_total
					tmp_counts['cpu_total'] += 1

				# handle POWER if present
				if 'power_util:consumption' in data:
					power_consumption = getInt(data, 'power_util:consumption')
					tmp_sums['power'] += power_consumption
					tmp_counts['power'] += 1
				
				# handle MEMORY if present
				if 'hardware:mem_size' in data:
					mem_size = computeCN.__convert(getInt(data, 'hardware:mem_size'), 10)
					tmp_sums['mem_size'] += mem_size
					tmp_counts['mem_size'] += 1
				if 'hardware_util:mem_free' in data:
					mem_free = computeCN.__convert(getInt(data, 'hardware_util:mem_free'), 20)
					tmp_sums['mem_free'] += mem_free
					tmp_counts['mem_free'] += 1				
					mem_cache = computeCN.__convert(getInt(data, 'hardware_util:mem_cache'), 20)
					tmp_sums['mem_cache'] += mem_cache
					tmp_counts['mem_cache'] += 1	
							
				# handle NETWORK if present
				if 'network_util:net_through' in data:
					net_through = computeCN.__convert(getInt(data, 'network_util:net_through'), 20)
					tmp_sums['net_through'] += net_through
					tmp_counts['net_through'] += 1	
			
				# handle VMs if persent
				vms = len([[k ,v] for k, v in data.items() if re.search('^vms:vm_uuid.[0-9][0-9]?', k)])
				if vms > 0:
					#tmp_sums['vms'] += vms
					#tmp_counts['vms'] += 1
					for i in range(vms):
						vmid = data['vms:vm_uuid.'+str(i)]
						if vmid in vmslist:
							vmslist[vmid][1] = index # set current index as end
						else:
							vmslist[vmid] = [index, index] # set current index as start and end
				
			except Exception as e:
				print "Exception while reading data for row %s" % key
				print e
				continue
		
		# calculate average for the last timebucket
		index = timebuckets - 1
		for key in metrics:
			if tmp_counts[key] == 0:
				result[key][index] = 0
			else:
				result[key][index] = int(tmp_sums[key] / tmp_counts[key])
		# fill mem_size with previous value if not present
		if result['mem_size'][index] == 0 and index > 0:
			result['mem_size'][index] = result['mem_size'][index-1]
		# calculate mem_used from used=(size-free)
		result['mem_used'][index] = result['mem_size'][index] - result['mem_free'][index]
		if result['mem_used'][index] < 0:
			result['mem_used'][index] = 0
		# calculate amount of VMs per time bucket
		for index in range(timebuckets):
			counter = 0
			for vmid in vmslist:
				vmtimes = vmslist[vmid]
				if vmtimes[0] <= index and vmtimes[1] >= index:
					counter += 1
			result['vms'][index] = counter	
	
	
		# reset caches
		tmp_sums = {}
		for key in metrics:
			tmp_sums[key] = 0
		tmp_counts = {}
		for key in metrics:
			tmp_counts[key] = 0

		endtime = datetime.now()
		
		logging.info('Counted %i elements' % counter)
		logging.info('Start %s End %s Diff: %s' % (starttime, endtime, endtime-starttime))
		
		return {
			'cpu': {'data': {'sys': result['cpu_sys'], 'usr': result['cpu_usr'], 'wio': result['cpu_wio'], 'total': result['cpu_total']}, 'ylabel': 'Percentage'},
			'power': {'data': result['power'], 'ylabel': 'Watts'},
			'vms': {'data': result['vms'], 'ylabel': 'Amount', 'list': vmslist},
			'network': {'data': result['net_through'], 'ylabel': 'MB/s'},
			'memory': {'data': {'size': result['mem_size'], 'free': result['mem_free'], 'cache': result['mem_cache'], 'used': result['mem_used']}, 'ylabel': 'GB'}
		}
		
def getInt(data, key):
	try:
		value = int(data[key])
	except:
		value = 0
	return value

