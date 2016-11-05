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

def requestVms(start, stop, vmslist):

	interval = int((int(stop) - int(start)) / timebuckets)

	dataplayMastersByInstance = {}
	dataplayLoadBalancerIdByInstance = {}
	dataplayRequestsByInstance = {}

	pool = happybase.ConnectionPool(size=10, host=host, port=port)
	with pool.connection() as connection:
		# query VMs for meta fields
		for vmid in vmslist:
			table = connection.table('VMHistory')
			vmtimes = vmslist[vmid]
			columns = [
				#'meta:applicationTypeInstance',			# applicationInstanceId
				#'meta:applicationType',				# application name, e.g. dataplay or molpro ?
				#'meta:applicationComponentInstance',		# instanceId ?
				#'meta:applicationComponent'			# lifecyclecomponent name, e.g. PgPool, Master, LoadBalancer
				'meta:AppInstance',
				'meta:AppName',
				'meta:Component',
			]			
			for key, data in table.scan(row_prefix=vmid+"-", columns=columns, batch_size=1000):
				row_timestamp = int(key.replace(vmid+'-', ''))
				if row_timestamp > stop:
					continue
				if 'meta:AppInstance' and 'meta:AppName' and 'meta:Component' in data:
					appName = data['meta:AppName']
					if appName != "DataPlay":
						continue
					appInstanceId = data['meta:AppInstance']
					appComponent = data['meta:Component']
					if appComponent == 'MasterNode':
						if not appInstanceId in dataplayMastersByInstance:
							dataplayMastersByInstance[appInstanceId] = [0]*timebuckets
							
						if row_timestamp < int(start):
							i = 0
						else:
							i = int( (row_timestamp-int(start)) / interval )
						while i <= vmtimes[1]: # until last appearance of VM
							dataplayMastersByInstance[appInstanceId][i] += 1
							i += 1
					if appComponent == 'LoadBalancer':
						if not appInstanceId in dataplayRequestsByInstance:
							dataplayRequestsByInstance[appInstanceId] = [0]*timebuckets
						dataplayLoadBalancerIdByInstance[appInstanceId] = vmid

		# query Req/s for LoadBalancer VMs
		for appInstanceId in dataplayLoadBalancerIdByInstance:
			vmid = dataplayLoadBalancerIdByInstance[appInstanceId]

			table = connection.table('VMAppHistory')
			columns = [
				#'app:HAPROXY-MASTER-TWO_XX_PER_SECOND',
				'app:HAPROXY-MASTER-SESSION_PER_SECOND'
				#,
				#'app:HAPROXY-GAMIFICATION-TWO_XX_PER_SECOND',
				#'app:HAPROXY-GAMIFICATION-SESSION_PER_SECOND'
			]
			
			requestsSumByAppId = 0
			requestsCountByAppId = 0
			index = 0
			
			# get all rows for this loadbalancer VM vmid
			row_start = vmid+'-'+start
			row_stop = vmid+'-'+stop
			for key, data in table.scan(row_start=row_start, row_stop=row_stop, columns=columns, batch_size=1000):
				row_timestamp = int(key.replace(vmid+'-', ''))
				try: 
					if ((row_timestamp - int(start)) > ((index + 1) * interval)):
						# calculate average
						if requestsCountByAppId == 0:
							avg = 0
						else:
							avg =  requestsSumByAppId / requestsCountByAppId
						dataplayRequestsByInstance[appInstanceId][index] = avg
						requestsSumByAppId = 0
						requestsCountByAppId = 0

						# search next time bucket
						while ((index < timebuckets) and ((row_timestamp - int(start)) > ((index + 1) * interval))):
							index += 1
				except Exception as e:
					print "Exception while computing average"
					print e
					continue				
				
				#requests = getFloat(data, 'app:HAPROXY-MASTER-TWO_XX_PER_SECOND')
				requests = getFloat(data, 'app:HAPROXY-MASTER-SESSION_PER_SECOND')
				if requests >= 0:
					requestsSumByAppId += requests
					requestsCountByAppId += 1
					
			# calculate average for the last index
			index = timebuckets - 1
			if requestsCountByAppId == 0:
				avg = 0
			else:
				avg =  requestsSumByAppId / requestsCountByAppId
			dataplayRequestsByInstance[appInstanceId][index] = avg
			requestsSumByAppId = 0
			requestsCountByAppId = 0		
		
	return {
		'dataplay': {
			'masters': dataplayMastersByInstance,
			'loadBalancerIds': dataplayLoadBalancerIdByInstance,
			'requests': dataplayRequestsByInstance
		}
	}
				

def request(start, stop):
	columns = ['app:molIn','app:deploymentstatus', 'app:vmId', 'app:masters', 'app:appInstanceId', 'app:frontends']

	interval = int((int(stop) - int(start)) / timebuckets)
	
	pool = happybase.ConnectionPool(size=10, host=host, port=port)
	with pool.connection() as connection:
	
		molproJobsPerType = {}
		molproJobsTotal = 0
		molproDeploymentsByStatus = {}
		molproVmIdList = []
		molproVmCounter = 0
		
		dataplayMastersByInstance = {}
		tmp_dataplayMastersByInstanceSum = {}
		tmp_dataplayMastersByInstanceCount = {}
	
		# Query VMAppHistory to get App Data
		table = connection.table('VMAppHistory')
		index = 0
		for key, data in table.scan(row_start=start, row_stop=stop, columns=columns, batch_size=1000):
			row_timestamp = int(key.split('-')[0])
			
			#################################################################
			# Molpro Specific Metrics
			if 'app:molIn' in data:
				molIn = data['app:molIn']
				molproJobsTotal += 1
				if molIn in molproJobsPerType:
					molproJobsPerType[molIn] += 1
				else:
					molproJobsPerType[molIn] = 1
			if 'app:deploymentstatus' in data:
				deploymentstatus = data['app:deploymentstatus']
				if deploymentstatus in molproDeploymentsByStatus:
					molproDeploymentsByStatus[deploymentstatus] += 1
				else:
					molproDeploymentsByStatus[deploymentstatus] = 1
			if 'app:vmId' in data:
				vmid = data['app:vmId']
				if vmid != 'null':
					molproVmIdList.append(vmid)
					molproVmCounter += 1
					
			#################################################################
			# DataPlay Specific Metrics
			
			# if we just crossed a time bucket border, group values and start on empty bucket for next time frame
			try: 
				if ((row_timestamp - int(start)) > ((index + 1) * interval)):
					# calculate average
					for avg_appInstanceId in tmp_dataplayMastersByInstanceSum:
						if tmp_dataplayMastersByInstanceCount[avg_appInstanceId] == 0:
							avg = 0
						else:
							avg = int(tmp_dataplayMastersByInstanceSum[avg_appInstanceId] / tmp_dataplayMastersByInstanceCount[avg_appInstanceId])
						if not avg_appInstanceId in dataplayMastersByInstance:
							dataplayMastersByInstance[avg_appInstanceId] = [0]*timebuckets
						dataplayMastersByInstance[avg_appInstanceId][index] = avg
						# reset caches
						tmp_dataplayMastersByInstanceSum[avg_appInstanceId] = 0
						tmp_dataplayMastersByInstanceCount[avg_appInstanceId] = 0

					# search next time bucket
					while ((index < timebuckets) and ((row_timestamp - int(start)) > ((index + 1) * interval))):
						index += 1
			except Exception as e:
				print "Exception while computing average"
				print e
				continue			
					
			if 'app:masters' in data:
				appInstanceId = data['app:appInstanceId']
				masters = getInt(data, 'app:masters')
				frontends = getInt(data, 'app:frontends')
				if not appInstanceId in tmp_dataplayMastersByInstanceSum:
					tmp_dataplayMastersByInstanceSum[appInstanceId] = 0
					tmp_dataplayMastersByInstanceCount[appInstanceId] = 0
				tmp_dataplayMastersByInstanceSum[appInstanceId] += masters
				tmp_dataplayMastersByInstanceCount[appInstanceId] += 1

		# calculate average for the last index
		index = timebuckets - 1
		for avg_appInstanceId in tmp_dataplayMastersByInstanceSum:
			if tmp_dataplayMastersByInstanceCount[avg_appInstanceId] == 0:
				avg = 0
			else:
				avg = int(tmp_dataplayMastersByInstanceSum[avg_appInstanceId] / tmp_dataplayMastersByInstanceCount[avg_appInstanceId])
			if not avg_appInstanceId in dataplayMastersByInstance:
				dataplayMastersByInstance[avg_appInstanceId] = [0]*timebuckets
			dataplayMastersByInstance[avg_appInstanceId][index] = avg
			# reset caches
			tmp_dataplayMastersByInstanceSum[avg_appInstanceId] = 0
			tmp_dataplayMastersByInstanceCount[avg_appInstanceId] = 0	
		
		# Query VMHistory to get the latest status for each Molpro VM
		molproVmStatesCounter = {}
		for vmId in molproVmIdList:
			state = getLatestVmStatus(connection, vmId, start, stop)
			if state in molproVmStatesCounter:
				molproVmStatesCounter[state] += 1
			else:
				molproVmStatesCounter[state] = 1	
	
	return {
		'molpro': {
			'jobsPerType': molproJobsPerType,
			'jobsTotal': molproJobsTotal,
			'deploymentsByStatus': molproDeploymentsByStatus,
			'vmCounter': molproVmCounter,
			'vmStatesCounter': molproVmStatesCounter		
		},
		'dataplay': {
			'masters_changes': dataplayMastersByInstance
		}
	}
	
def getLatestVmStatus(connection, vmId, start, stop):
	table = connection.table('VMHistory')
	state = ''
	isDeleted = False
	for key, data in table.scan(row_start=vmId+"-"+start, row_stop=vmId+"-"+stop, columns=['meta:vm_state', 'meta:isDeleted'], batch_size=1000):
		if 'meta:vm_state' in data:
			state = data['meta:vm_state']
		if 'meta:isDeleted' in data and data['meta:isDeleted'] == "true":
			isDeleted = True
			
	# VM got deleted without a proper shut down.
	if isDeleted and (state == "running" or state == "failure"):
		state = "shut"
	return state
	
			
			
def getInt(data, key):
	try:
		value = int(data[key])
	except:
		value = 0
	return value

def getFloat(data, key):
	try:
		value = float(data[key])
	except:
		value = float(0)
	return value
