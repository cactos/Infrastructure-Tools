import re
from collections import Counter

# import models
from models.computenodes.computenode import *
from models.virtualmachines.virtualmachine import *

import data.compute_cn as data

'''
build overview
'''
def renderClusterOverview():
	out = {
			'cns': clusterCN(),
			'cpu': clusterCPU(),
			'memory': clusterMemory(),
			'network': clusterNetwork(),
			'power': clusterPower(),
			'filesystem': clusterFilesystem(),
			'storage': clusterStorage(),
			'vms': clusterVM()
			}
	return out

'''
build computenode history
'''
def buildCNHistory(c):
	out = {	'cpu': computeDetailCPU(c),
			'memory': data.computeDetailMemory(c),
			'network': data.computeDetailNetwork(c),
			'power': computeDetailPower(c),
			'filesystem': computeDetailFilesystem(c),
			'storage': computeDetailStorage(c)
		 }
	return out


'''
general computenote data for cluster
'''
def clusterCN():
	global cnSnapshots
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		if c.meta['meta:state'] == 'running':
			tmp.append({'cn_running': 1,
				'cn_paused': 0,
				'cn_shut': 0,
                'cn_maintenance': 0
				})
		if c.meta['meta:state'] == 'paused':
			tmp.append({'cn_running': 0,
				'cn_paused': 1,
				'cn_shut': 0,
                'cn_maintenance': 0
				})
		if c.meta['meta:state'] == 'shut':
			tmp.append({'cn_running': 0,
				'cn_paused': 0,
				'cn_shut': 1,
                'cn_maintenance': 0
				})
		if c.meta['meta:state'] == 'maintenance':
			tmp.append({'cn_running': 0,
				'cn_paused': 0,
				'cn_shut': 1,
                'cn_maintenance': 1
				})
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	out.update({'total_amount': len(cnSnapshots)})
	return out

'''
compute cpu usage of cluster
'''
def clusterCPU():
	global cnSnapshots 
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		sys = int(c.hardware['hardware_util:cpu_sys'])
		usr = int(c.hardware['hardware_util:cpu_usr'])
		wio = int(c.hardware['hardware_util:cpu_wio'])
		free = 100 - sys - usr - wio
		complete = sys + usr + wio

		tmp.append({'cpu_cores': int(c.hardware['hardware:cpu_cores']),
			'cpu_freq': float(c.hardware['hardware:cpu_freq']),
			'cpu_sys': sys,
			'cpu_usr': usr,
			'cpu_wio': wio,
			'cpu_free': free,
			'cpu_complete': complete
			})
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out

'''
compute single computenode history
'''
def computeDetailCPU(c):
		sys = int(c.hardware['hardware_util:cpu_sys'])
		usr = int(c.hardware['hardware_util:cpu_usr'])
		wio = int(c.hardware['hardware_util:cpu_wio'])
		free = 100 - sys - usr - wio
		complete = sys + usr + wio

		tmp = {'cpu_cores': int(c.hardware['hardware:cpu_cores']),
			'cpu_freq': float(c.hardware['hardware:cpu_freq']),
			'cpu_sys': sys,
			'cpu_usr': usr,
			'cpu_wio': wio,
			'cpu_free': free,
			'cpu_complete': complete
			}
		return tmp
'''
compute memory usage of cluster
'''
def clusterMemory():
	global cnSnapshots
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		tmp.append(data.computeDetailMemory(c))
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out

'''
compute network usage of cluster
'''
def clusterNetwork():
	global cnSnapshots
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		tmp.append(data.computeDetailNetwork(c))
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out

'''
compute power usage of cluster
'''
def clusterPower():
	global cnSnapshots
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		try:			
			if c.power['power_util:consumption'] != '-':
				tmp.append({'power_consumption': int(c.power['power_util:consumption']),
					'power_cap0': int(c.power['power:capacity.0']),
	   				'power_cap1': int(c.power['power:capacity.1'])})
			else:
				tmp.append({'power_cap0': int(c.power['power:capacity.0']),
					'power_cap1': int(c.power['power:capacity.1'])})
		except:
			pass
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out
'''
compute power for single computenode
'''
def computeDetailPower(c):
	tmp = {}
	try:			
		if c.power['power_util:consumption'] != '-':
			tmp = {'power_consumption': int(c.power['power_util:consumption']),
				'power_cap0': int(c.power['power:capacity.0']),
				'power_cap1': int(c.power['power:capacity.1'])}
		else:
			tmp = {'power_consumption': float(0.0),
					'power_cap0': int(c.power['power:capacity.0']),
					'power_cap1': int(c.power['power:capacity.1'])}
	except:
		pass
	return tmp

'''
comppute filesystem usage of cluster
'''
def clusterFilesystem():
	global cnSnapshots
	tmp = []
	for cn in cnSnapshots:
		c  = cnSnapshots[cn]
		amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
		for i in range(amount):
			avail = data.__convert(int(c.filesystem['filesystem:available.'+str(i)]), 20)*float(1.073741824) 
			used = data.__convert(int(c.filesystem['filesystem:used.'+str(i)]), 20)*float(1.073741824)
			full = avail + used
			tmp.append({'available': avail,
					'used': used,
					'fsSize': full,
					'readmax': float(c.filesystem['filesystem:readbandmax.'+str(i)].replace(' MB/s', '')),
					'writemax': float(c.filesystem['filesystem:writebandmax.'+str(i)].replace(' MB/s', ''))
					})
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out

'''
filesystem history for single computenode
'''
def computeDetailFilesystem(c):
	tmp = {}
	amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
	for i in range(amount):
		avail = data.__convert(int(c.filesystem['filesystem:available.'+str(i)]), 20)*float(1.073741824) 
		used = data.__convert(int(c.filesystem['filesystem:used.'+str(i)]), 20)*float(1.073741824)
		full = avail + used
		tmp.update({'available_'+str(i): avail,
						'used_'+str(i): used,
						'fsSize_'+str(i): full,
						'readmax_'+str(i): float(c.filesystem['filesystem:readbandmax.'+str(i)].replace(' MB/s', '')),
						'writemax_'+str(i): float(c.filesystem['filesystem:writebandmax.'+str(i)].replace(' MB/s', ''))
						})
	return tmp

'''
compute storage info of cluster
'''
def clusterStorage():
	global cnSNapshots
	tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
		for i in range(amount):
			fs = c.filesystem['filesystem:mount.'+str(i)]
			parentIndex = data.__getParentIndex(c, fs)
			if not parentIndex == -1:
				tmp.append({'disk_kbrs': float(data.__getDiskMountValues(c, parentIndex, 'kbrs')),
					'disk_kbws': float(data.__getDiskMountValues(c, parentIndex, 'kbws')),
					'disk_tps': float(data.__getDiskMountValues(c, parentIndex, 'tps'))
					 })
	out = Counter()
	for t in tmp:
		out.update(t)
	out = dict(out)
	return out

'''
compute storage istory for single computenode
'''
def computeDetailStorage(c):
	tmp = {}
	amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
	for i in range(amount):
		fs = c.filesystem['filesystem:mount.'+str(i)]
		parentIndex = data.__getParentIndex(c, fs)
		if not parentIndex == -1:
			tmp.update({'disk_kbrs_'+str(i): float(data.__getDiskMountValues(c, parentIndex, 'kbrs')),
				'disk_kbws_'+str(i): float(data.__getDiskMountValues(c, parentIndex, 'kbws')),
				'disk_tps_'+str(i): float(data.__getDiskMountValues(c, parentIndex, 'tps'))
				 })
	return tmp

'''
compute vm info of cluster
'''
def clusterVM():
	global cnSnapshots
	global vmSnapshots
	tmp = []
	vm_tmp = []
	for cn in cnSnapshots:
		c = cnSnapshots[cn]
		tmp.append({'absolute_vms': len([[k, v] for k, v in c.vms.items() if re.search('^vms:vm_uuid.[0-9][0-9]?', k)])			
			})
	a = Counter()
	for t in tmp:
		a.update(t)
	a = dict(a)
	
	if not vmSnapshots:
		vm_tmp.append({'vms_running': 0,
			'vms_paused': 0,
			'vms_shut': 0,
			'vms_na': 0,
			'vms_failure': 0
			})
		
	for vm in vmSnapshots:
		v = vmSnapshots[vm]
		try:
			if v.meta['meta:vm_state'] == 'running':
				vm_tmp.append({'vms_running': 1,
					'vms_paused': 0,
					'vms_shut': 0,
					'vms_na': 0,
					'vms_failure': 0
					})
			if v.meta['meta:vm_state'] == 'paused':
				vm_tmp.append({'vms_running': 0,
					'vms_paused': 1,
					'vms_shut': 0,
					'vms_na': 0,
					'vms_failure': 0
					})
			if v.meta['meta:vm_state'] == 'shut':
				vm_tmp.append({'vms_running': 0,
					'vms_paused': 0,
					'vms_shut': 1,
					'vms_na': 0,
					'vms_failure': 0
					})
			if v.meta['meta:vm_state'] == 'failure':
					vm_tmp.append({'vms_running': 0,
						'vms_paused': 0,
						'vms_shut': 0,
						'vms_na': 0,
						'vms_failure': 1
						})
		except:
			vm_tmp.append({'vms_running': 0,
						'vms_paused': 0,
						'vms_shut': 0,
						'vms_na': 1
						})
		
	out = Counter()
	for t in vm_tmp:
		out.update(t)
	out = dict(out)
	'''add total number of vms'''
	out.update({'total_amount': len(vmSnapshots)})
	return out
