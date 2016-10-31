import re
from collections import Counter

from models.virtualmachines.virtualmachine import *

'''
data aggregation for VM overview in computenode
@param c computenode object
@param vm dict of vms
'''
def computeVMData(c, vm):
	global vmSnapshots
	vmDict = []
        vmNames = []
	amount = len([[k ,v] for k, v in c.vms.items() if re.search('^vms:vm_uuid.[0-9][0-9]?', k)])
	for i in range(amount):
		vmName = c.vms['vms:vm_uuid.'+str(i)]
                vmNames.append(vmName)
		'''get vm object from vm dict'''
        # for vmName in sorted(vmNames):
		try:
			vm = vmSnapshots[vmName]
			vmDict.append({'vm_uuid': c.vms['vms:vm_uuid.'+str(i)],
				'id': i,
				'hardware': computeVMHardware(vm),
				'meta': computeVMMeta(vm),
				'network': computeVMNetwork(vm),
				'storage': computeVMStorage(vm)
			})
		except:
			print 'vm '+ vmName + ' not found'
	return vmDict

'''
data aggregation for single vm
'''
def renderSingleVM(vmName):
    global vmSnapshots
    vmDict = {}
    try:
        vm = vmSnapshots[vmName]
        vmDict = {'hardware': computeVMHardware(vm),
				'meta': computeVMMeta(vm),
				'network': computeVMNetwork(vm),
				'storage': computeVMStorage(vm)                
                }
    except:
        vmDict = None
    return vmDict

'''
build VM history
'''
def buildVMHistory(vm):
    out = {'hardware': vmHardwareHistory(vm),
            'network': vmNetworkHistory(vm),
            'storage': vmStorageHistory(vm)
            }
    return out

'''
history functions
'''
def vmHardwareHistory(vm):
    try:
            total = float(vm.hardware['hardware:ram-total'].replace('MB', ''))
            used = float(vm.hardware['hardware:ram-used'].replace('MB', ''))
            free = total - used
            percentage = (used / total)*100

            out = {'cpuCS': float(vm.hardware['hardware:CpuCS']),
                       'ram_total': total,
                       'ram_used': used,
                       'ram_available': free,
                       'ram_percentage': percentage,
                       'cpu_vm': float(vm.hardware['hardware:CpuVM'].replace('%', '')),
                     }
    except:
            out = {}
    return out

def vmNetworkHistory(vm):
    return computeVMNetwork(vm)

def vmStorageHistory(vm):
    return computeVMStorage(vm)

'''
render vm overview
@param vms dict of vms
'''
def renderVM(vms):
	vmDict = []
	i = 1
	for v in vms:
		vm = vmSnapshots[v] 
		try:
			if vm.meta['meta:vm_state'] != 'running':
				vmDict.append({'vm_uuid': vm,
					'id': i,
					'meta': computeVMMeta(vm)					
					})
			else:
				vmDict.append({'vm_uuid': vm.hardware['hardware:UUID'],
						'id': i,
						'hardware': computeVMHardware(vm),
						'meta': computeVMMeta(vm),
						'network': computeVMNetwork(vm),
						'storage': computeVMStorage(vm)
					})
			i = i+1
		except:
			print 'vm not found'
	return vmDict

'''
hardware data of virtual machine
'''
def computeVMHardware(vm):
	try:
		total = round(float(vm.hardware['hardware:ram-total'].replace('MB', '')), 3)
		used = round(float(vm.hardware['hardware:ram-used'].replace('MB', '')), 3)
		free = total - used
		percentage = (used / total)*100

		out = {'cpuCS': vm.hardware['hardware:CpuCS'],
			   'ram_total': total,
			   'ram_used': used,
			   'ram_available': free,
			   'ram_percentage': percentage,
			   'cpu_vm': float(vm.hardware['hardware:CpuVM'].replace('%', '')),
			   'vmname': vm.hardware['hardware:vmname'],
               'uuid': vm.hardware['hardware:UUID']
			 }
	except:
		out = {}
	return out

'''
meta data of virtual machine
'''
def computeVMMeta(vm):
	out = {'source': vm.meta['meta:csource'],
			'vm_state': vm.meta['meta:vm_state']
			}
	try:
		out.update({'deleted': vm.meta['meta:isDeleted']})
	except:
		pass
	return out

'''
network data of virtual machine
'''
def computeVMNetwork(vm):
	try:
		out = {'network': float(vm.network['network:network'].replace('MB/s', ''))
				}
	except:
		out = {}
	return out

'''
storage data of virtual machine
'''
def computeVMStorage(vm):
	try:
		total = round(float(vm.storage['storage:disk-total'].replace('MB', '')), 3)
		used = round(float(vm.storage['storage:disk-used'].replace('MB', '')), 3)
		free = total - used
		percentage = (used/total)*100
		out = {'disk_read': float(vm.storage['storage:disk-read'].replace('MB/s', '')),
				'disk_write': float(vm.storage['storage:disk-write'].replace('MB/s', '')),
				'disk_total': total,
				'disk_used': used ,
				'disk_available': free,
				'disk_percentage': percentage
				}
	except:
			out = {}
	return out
