import os
import sys
import glob
import happybase
import datetime

from app import cfg

from models.computenodes.computenode import *
from models.virtualmachines.virtualmachine import *

import data.compute_overview as ov
import data.compute_vm as compVM

from time import sleep
from collections import OrderedDict
import pprint
import pickle


def checkConnection():
	hostname = cfg['servers']['thrift']
	port = cfg['servers']['thriftport']
	print 'checking host'
	response = os.system("ping -c 1 " + hostname)
	if response == 0:
		print hostname + ' is up'
		return True
	else:
		print hostname + ' is down'
		return False

host = cfg['servers']['thrift']
port = cfg['servers']['thriftport']
sleeper = cfg['worker']['sleeper']

pool = happybase.ConnectionPool(size=10, host=host, port=port)

storagePath = cfg['paths']['storagePath']
maxHistory = 59

"""
main loop for reading Snapshot from HBase with connection pool
"""
def mainloop():
	global cnSnapshots
	global vmSnapshots
	with pool.connection() as connection:
			while True:
				cnSnapshots.clear()
				table_cn = connection.table('CNSnapshot')
				for cnKey, cnData in table_cn.scan():
					__process_cn_snapshot(cnKey, cnData)
				
				vmSnapshots.clear()
				table_vm = connection.table('VMSnapshot')
				for vmKey, vmData in table_vm.scan():
					__process_vm_snapshot(vmKey, vmData)

				'''delete old vm history files that no longer exists'''
				__delVMHistory()
				__delCNHistory()

				#create History for ComputeNodes
				__writeCNHistory()
				# Cluster history
				__writeClusterHistory()
				#create history for VM's
				__writeVMHistory()

				sleep(sleeper)
			try:
				connection.close()
			except Exception as e:
				print '\nUnable to close connection\n'
				print e

"""
Process Computenode Data
"""
def __process_cn_snapshot(rowKey, rowData):
	global cnSnapshots
	tmpObject = Computenode(rowKey)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('filesystem:'))
	tmpObject.update_filesystem(r)	
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('hardware'))
	tmpObject.update_hardware(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('network'))
	tmpObject.update_network(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('meta'))
	tmpObject.update_meta(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('power'))
	tmpObject.update_power(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('storage'))
	tmpObject.update_storage(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('vms:'))
	tmpObject.update_vms(r)

"""
Process VM Snapshot Data
"""
def __process_vm_snapshot(rowKey, rowData):
	global vmSnapshots
	tmpObject = VirtualMachine(rowKey)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('hardware:'))
	tmpObject.update_vm_hardware(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('meta'))
	tmpObject.update_vm_meta(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('network:'))
	tmpObject.update_vm_network(r)
	r = dict((k, v) for k, v in rowData.iteritems() if k.startswith('storage:'))
	tmpObject.update_vm_storage(r)

'''
writes history to pickle
'''
def __writeClusterHistory():
	try:
		tmp = []
		fname = storagePath + 'history.p'
		if not os.path.exists(fname):
				open(fname, 'w').close()
		with open(fname, 'rb') as f:
			 while True:
				try: 
					tmp.append(pickle.load(f))
				except EOFError:
					break
		f.close()
		if len(tmp) > maxHistory:
			tmp.pop(0)

		overviewObject = ov.renderClusterOverview()
		
		with open(fname, 'wb') as f:
			for o in tmp:
					pickle.dump(o, f)	
			f.close()
		with open(fname, 'ab') as f:
	   		pickle.dump(overviewObject, f)
		f.close()
	except Exception as ex:
		print "error writing cluster history data"
		print ex
		pass

'''
writes each CN to pickle
'''
def __writeCNHistory():
	global cnSnapshots
	for c in cnSnapshots:
			try:
				tmp = []
				c = cnSnapshots[c]
				'''if stet not set do this'''
				if not c.meta:
					# print "set na meta to running"
					c.meta.update({'meta:state': 'maintenance'})
				if (c.meta['meta:state'] == 'running'):
					fname = storagePath + c.name + '.p'
					'''check if file exists for computenode'''
					if not os.path.exists(fname):
							open(fname, 'w').close()
					with open(fname, 'rb') as fr:
							while True:
									try: 
										tmp.append(pickle.load(fr))
									except EOFError:
										fr.close()
										break
					if len(tmp) > maxHistory:
							tmp.pop(0)

					cnObject = ov.buildCNHistory(c)
					with open(fname, 'wb') as fr:
						for o in tmp:
								pickle.dump(o, fr)
						fr.close()
					with open(fname, 'ab') as fr:
						pickle.dump(cnObject, fr)
						fr.close()
			except Exception as ex:
				print "error writing cn history data: " + c.name  
				print ex
				pass

'''write VM History'''
def __writeVMHistory():
	global vmSnapshots
	for vm in vmSnapshots:
		try:
			tmp = []
			vm = vmSnapshots[vm]
			'''vm state is important due to lack of data'''
			if vm.meta['meta:vm_state'] and (vm.meta['meta:vm_state'] == 'running'):
				fname = storagePath + vm.name + '.p'
				'''check if file exists for vm'''
				if not os.path.exists(fname):
						open(fname, 'w').close()
				with open(fname, 'rb') as vmf:
						while True:
								try:
										tmp.append(pickle.load(vmf))
								except EOFError:
										vmf.close()
										break
				if len(tmp) > maxHistory:
						tmp.pop(0)

				vmObject = compVM.buildVMHistory(vm)
				with open(fname, 'wb') as vmf:
					for o in tmp:
							pickle.dump(o, vmf)
					vmf.close()
				with open(fname, 'ab') as vmf:
					pickle.dump(vmObject, vmf)
					vmf.close()

		except Exception as ex:
			print "error writing vm history data: " + vm.name
			print ex
			pass
'''
delete vm that no longer exists
'''
def __delVMHistory():
	global vmSnapshots
	storageVMFiles = [ f[:-2] for f in os.listdir(storagePath) if not f.startswith("compute") and not f.startswith("__init") and not f.startswith('history')]
	diff = set(storageVMFiles) - set(vmSnapshots)
	for f in diff:
		try:
			os.remove(storagePath + f + '.p')
		except Exception as ex:
			print datetime.datetime.now() ,'- error deleting vm history'
			print ex 
			pass

'''
delete cn history that no longer exists
'''
def __delCNHistory():
	global cnSnapshots
	storageCNFiles = [f[:-2] for f in os.listdir(storagePath) if f.startswith("compute")]
	diff = set(storageCNFiles) - set(cnSnapshots)
	for f in diff:
		try:
			os.remove(storagePath + f + '.p')
			del cnSnapshots[f]
		except:
			pass

'''
delete cluster history
'''
def delClusterHistory():
	storageClusterHistoryFile = storagePath + 'history.p'
	try:
		os.remove(storageClusterHistoryFile)
	except:
		pass
