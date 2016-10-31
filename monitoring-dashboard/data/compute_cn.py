import re

'''
data aggregation for snapshot overview
@param computenode object
'''
def computeData(c):
	out = []
	fsav = [[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)]
	# print c.filesystem	
	amount = len(fsav)
	dataDict = []
	for i in range(amount):
		dataDict.append({'available': int(c.filesystem['filesystem:available.'+str(i)])*float(1.073741824),
			'used': int(c.filesystem['filesystem:used.'+str(i)])*float(1.073741824),
			'mount': c.filesystem['filesystem:mount.'+str(i)],
			'readmax': c.filesystem['filesystem:readbandmax.'+str(i)],
			'writemax': c.filesystem['filesystem:writebandmax.'+str(i)],
			'arch': c.hardware['hardware:cpu_arch'],
			'memsize': int(c.hardware['hardware:mem_size']),
			'memfree': int(c.hardware['hardware_util:mem_free']),
			'memcache': int(c.hardware['hardware_util:mem_cache']),
			'id': i,
			'netThrough': int(c.network['network_util:net_through']),
			'netSpeed': int(c.network['network:netw_speed'].replace('Mb/s', '')),
			'vms': len([[k ,v] for k, v in c.vms.items() if re.search('^vms:vm_uuid.[0-9][0-9]?', k)])
			})
	out.append({'name': c.name, 'data': dataDict, 'cpu': computeDetailCPU(c), 'meta': computeDetailMeta(c)})
	return out

'''
cpu data aggregation for detail view for computenode
'''
def computeDetailCPU(c):
	cpu_complete =  int(c.hardware['hardware_util:cpu_sys'])+int(c.hardware['hardware_util:cpu_usr'])+int(c.hardware['hardware_util:cpu_wio'])

	out = {'cpu_arch': c.hardware['hardware:cpu_arch'],
			'cpu_cores': int(c.hardware['hardware:cpu_cores']),
			'cpu_freq': float(c.hardware['hardware:cpu_freq']),
			'cpu_sys': int(c.hardware['hardware_util:cpu_sys']),
			'cpu_usr': int(c.hardware['hardware_util:cpu_usr']),
			'cpu_wio': int(c.hardware['hardware_util:cpu_wio']),
			'cpu_complete': cpu_complete
			}
	return out

'''
memory data aggregation for detail view for computenode
'''
def computeDetailMemory(c):
	msize = __convert(int(c.hardware['hardware:mem_size']), 10)
	mfree = __convert(int(c.hardware['hardware_util:mem_free']), 20)
	mused = msize-mfree
	percentage = (mused/msize)*100
	out = {'memsize': msize,
			'memfree': mfree,
			'memcache': __convert(int(c.hardware['hardware_util:mem_cache']), 20),
			'memused': mused,
			'percentage': percentage
			}
	return out

'''
meta data for computenode
'''
def computeDetailMeta(c):
    try:
	out = {'state': c.meta['meta:state']}
    except:
        out = {'state': 'not_found'}
    return out

'''
convert and scale up to given faktor
e.g kb -> Gb
'''
def __convert(v, p):
	x = (float(v) / (2 ** p))
	return x

'''
network data aggregation for detail view for computenode
'''
def computeDetailNetwork(c):
	out = {'netSpeed': int(c.network['network:netw_speed'].replace('Mb/s', ''))*0.125,
		'netThrough': round(__convert(int(c.network['network_util:net_through']), 20), 3)
                } 
	return out

'''
power data aggregation for detail view for computenode
'''
def computeDetailPower(c):
	try:	
		out = {'power_available': 'True',
				'power_cap0': int(c.power['power:capacity.0']),
				'power_cap1': int(c.power['power:capacity.1']),
				'power_serial0': c.power['power:serial.0'],
				'power_serial1': c.power['power:serial.1'],
				'power_consumption': c.power['power_util:consumption']
				} 
	except:
		out = {'power_available': 'False'}
	return out

'''
filesystem data aggregation for detail view for computenode
'''
def computeDetailFilesystem(c):
	out = []
	amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
	for i in range(amount):
		avail = __convert(int(c.filesystem['filesystem:available.'+str(i)]), 20) * float(1.073741824) 
		used = __convert(int(c.filesystem['filesystem:used.'+str(i)]), 20) * float(1.073741824)
		full = avail + used
		percentage = (used / full)*100
		out.append({'available': avail,
			'used': used,
			'fsSize': full,
			'percentage': percentage,
			'mount': c.filesystem['filesystem:mount.'+str(i)],
			'readmax': c.filesystem['filesystem:readbandmax.'+str(i)],
			'writemax': c.filesystem['filesystem:writebandmax.'+str(i)],
			'id': i})
		return out

'''
storage data aggregation for detail view for computenode
'''
def computeDetailStorage(c):
	out = []
	amount = len([[k, v] for k, v in sorted(c.filesystem.items()) if re.search('^filesystem:available.[0-9]?', k)])
	for i in range(amount):
		fs = c.filesystem['filesystem:mount.'+str(i)]
		parentIndex = __getParentIndex(c, fs)
		if parentIndex == -1:
			out.append({'filesystem_mount': fs,
				'disk_mount': 'network mount',
				'fs_type': c.filesystem['filesystem:type.'+str(i)],
				'id': i})
		else:
			out.append({'filesystem_mount': fs,
				'disk_mount': __getDiskMountValues(c, parentIndex),
				'disk_size': __getDiskMountValues(c, parentIndex, 'size'),
				'disk_name': __getDiskMountValues(c, parentIndex, 'name'),
				'disk_type': __getDiskMountValues(c, parentIndex, 'type'),
				'disk_kbrs': __getDiskMountValues(c, parentIndex, 'kbrs'),
				'disk_kbws': __getDiskMountValues(c, parentIndex, 'kbws'),
				'disk_tps': __getDiskMountValues(c, parentIndex, 'tps'),
				'id': i})
	return out

'''
get Index for storage Values
@return: Index or -1 if not available
'''
def __getParentIndex(c, mountValue):
	if mountValue == '/var/lib/nova/instances':
		return -1 
	try:
		storageMount = [k for k, v in c.storage.items() if (mountValue==v and k.startswith('storage:disk_mount'))] 
		parentIndex = storageMount[0].replace('storage:disk_mount.', '')
	except:
		return -1
	return parentIndex

'''
computes storage data for logical volume

Modes (str): 
	default: get disk parent
	size: get disk size
	name: get disk name
	type: get disk type
	kbrs: get kb read per second
	kbws: get kb written per second
	tps: get transaction per second

@param c object
qparam mountValue value of mount
'''
def __getDiskMountValues(c, parentIndex, mode=None):
	if mode is None:
		parent = c.storage['storage:disk_parent.'+parentIndex]
		return parent
	if mode == 'size':
		size = c.storage['storage:disk_size.'+parentIndex]
		return size
	if mode == 'name':
		name = c.storage['storage:disk_name.'+parentIndex]
		return name
	if mode == 'type':
		typ = c.storage['storage:disk_type.'+parentIndex]
		return typ
	if mode == 'kbrs':
		kbr = c.storage['storage_util:kB_read/s.'+parentIndex]
		return kbr
	if mode == 'kbws':
		kbw = c.storage['storage_util:kB_wrtn/s.'+parentIndex]
		return kbw
	if mode == 'tps':
		tps = c.storage['storage_util:tps.'+parentIndex]
		return tps
