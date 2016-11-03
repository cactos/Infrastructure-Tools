import os
from app import app, cfg

import time
import happybase

from flask import Flask, render_template, request, url_for, abort
import pprint
import re

import json
import pickle

#used for thrift
import worker.connection as worker
import thread
import collections

# import models
from models.computenodes.computenode import *
from models.virtualmachines.virtualmachine import *

# import data aggregation
import data.compute_cn as computecn
import data.compute_vm as computevm
import data.compute_overview as computeov
import data.compute_history as computeHistory
import data.app_history as appHistory

import logging
from datetime import datetime


storagePath = cfg['paths']['storagePath']
host = cfg['app']['host']
port = int(cfg['app']['port'])
serverhost = cfg['servers']['thrift']
serverport = cfg['servers']['thriftport']

@app.route('/')
@app.route('/overview')
def ahistory():
    headless = request.args.get('headless')
    print "headless param %s" % headless	
    return render_template('ajaxhistory.html', headless=headless)

@app.route('/snapshots')
def snapshots():
	headless = request.args.get('headless')
	global cnSnapshots
	entries = []
	for k in sorted(cnSnapshots):
		out = computecn.computeData(cnSnapshots[k])
		entries.append(out)
	return render_template('snapshots.html', entries=entries, headless=headless)

@app.route('/virtualmachines')
def virtualmaschines():
	global vmSnapshots
	headless = request.args.get('headless')
	vms = computevm.renderVM(sorted(vmSnapshots))
	return render_template('vmSnapshots.html', vms=vms, headless=headless)

@app.route('/snapshots/computenode<id>')
def snComputeNode(id):
    global cnSnapshots
    global vmSnapshots
    headless = request.args.get('headless')
    vms = []
    c = cnSnapshots['computenode'+id]
    entries = {'cpu': computecn.computeDetailCPU(c),
        'memory': computecn.computeDetailMemory(c),
        'network': computecn.computeDetailNetwork(c),
        'power': computecn.computeDetailPower(c),
        'filesystem': computecn.computeDetailFilesystem(c),
        'storage': computecn.computeDetailStorage(c)}
    try: 
        entries.append({'meta': computecn.computeDetailMeta(c)})
    except:
        pass
    staticData = computecn.computeData(c)
    vm = computevm.computeVMData(c, sorted(vmSnapshots))
    return render_template('computenode.html',name='Computenode'+id, entries=entries, sd=staticData, vms=vm, headless=headless)

@app.route('/snapshots/vm/<id>')
def snVMs(id):
    headless = request.args.get('headless')
    entries = []
    vm = computevm.renderSingleVM(id)
    '''if vm is not found'''
    if vm is None:
        return "VM not found"
    return render_template('virtualmachine.html', vm=vm, headless=headless) 

@app.route('/rangehistory', methods=['GET', 'POST'])
def rangehistory():
    headless = request.args.get('headless')
    global cnSnapshots
    entries = []
    for k in sorted(cnSnapshots):
            out = computecn.computeData(cnSnapshots[k])
            entries.append(out)
    
    if request.method == 'GET':
        return render_template('rangehistory.html', entries=entries, headless=headless)

    if request.method == 'POST':
        rawData = request.form['daterange']
        cnVal = str(request.form['computenode'])
        print cnVal
        modeVal = str(request.form['mode'])
        metric = str(request.form['metric'])

        rawTimes = rawData.split(" - ")
        rawStart = rawTimes[0]
        rawEnd = rawTimes[1]
        start = str(int(time.mktime(time.strptime(rawStart, '%m-%d-%Y %H:%M:%S'))) * 1000)
        stop = str(int(time.mktime(time.strptime(rawEnd, '%m-%d-%Y %H:%M:%S'))) * 1000)
        try:
            history = computeHistory.requestHistory(cnVal, start, stop, modeVal, metric)
        except Exception as e:
            return "error loading data: "+e
        if history is None:
            error = {'message': 'No Data in chosen Timerange Available'}
            return render_template('rangehistory.html', entries=entries, error=error, headless=headless)
        # return json.dumps(computeHistory.requestHistory(cnVal, start, stop, modeVal))
        return render_template('rangehistory.html', entries=entries, history=history, headless=headless)

'''
CNlistHistory get cns in given timerange
set: used to create unique list entries
'''
@app.route('/getCNListHistory/<date>')
def getCNListHistory(date):
    cnAmount = [[0] for i in range(60)]
    index = 0
    tmp = [0]
    cnList = set()
    
    rawTimes = date.split(" - ")
    rawStart = rawTimes[0]
    rawEnd = rawTimes[1]
    start = str(int(time.mktime(time.strptime(rawStart, '%m-%d-%Y %H:%M:%S'))) * 1000)
    stop = str(int(time.mktime(time.strptime(rawEnd, '%m-%d-%Y %H:%M:%S'))) * 1000)
    
    interval = int((int(stop) - int(start)) / 60)
    
    pool = happybase.ConnectionPool(size=10, host=serverhost, port=serverport)
    with pool.connection() as connection:
            t2 = connection.table('CNListHistory')
            for key, data in t2.scan(row_start=start, row_stop=stop):
                # print key, data
                cnAddList = set(data['cns:list'].split(','))
                cnList = set(cnList | cnAddList)
                
                ts = int(key)
                if ((ts - int(start)) < ((index + 1) * interval)):
                    tmp.append(len(data['cns:list'].split(',')))
                else:
                    cnAmount[index] = tmp
                    index += 1
                    while ((index < 60) and ((ts - int(start)) >= ((index + 1) * interval))):
                        cnAmount[index] = tmp
                        index += 1
                    tmp = []
                    tmp.append(len(data['cns:list'].split(',')))
	    # fill last fields of timerange with the last value we had
	    while (index < 60):
		cnAmount[index] = tmp
                index += 1

    print cnAmount
    ''' need useful chunk size min time is 1 hour module writes every 10 minutes to hbase'''
    maxcnAmount = []
    currentIndex = 0
    firstValueIndex = 0
    firstValue = 0
    for cn in cnAmount:
	value = max(cn)
	if firstValueIndex == 0 and value > 0:
		firstValueIndex = currentIndex
		firstValue = value
	currentIndex += 1
        maxcnAmount.append(value)
    # fill first few fields if they were null
    currentIndex = 0
    while currentIndex <= firstValueIndex:
	maxcnAmount[currentIndex] = value
	currentIndex += 1

    # query historical data for all compute nodes
    cns = sorted(list(cnList))
    history = computeHistory.requestHistoryForNodes(cns, start, stop)

    # query historical data for applications
    apphistory = appHistory.request(start, stop)
    apphistoryVms = appHistory.requestVms(start, stop, history['vmslist'])
    apphistory['dataplay'].update(apphistoryVms['dataplay'])

    # create json result
    out = {'cns': {'cnList': cns, 'cnAmount': maxcnAmount}, 'history': history, 'apphistory': apphistory }
    return json.dumps(out)


'''
get data for rangehistory via angular
'''
@app.route('/requestrangehistory/cn/<cn>/mode/<mode>/metric/<metric>/date/<date>')
def getrangehistory(cn, mode, metric, date):
    print cn
    rawTimes = date.split(" - ")
    rawStart = rawTimes[0]
    rawEnd = rawTimes[1]
    start = str(int(time.mktime(time.strptime(rawStart, '%m-%d-%Y %H:%M:%S'))) * 1000)
    stop = str(int(time.mktime(time.strptime(rawEnd, '%m-%d-%Y %H:%M:%S'))) * 1000)

    try:
        history = computeHistory.requestHistory(cn, start, stop)
    except Exception as e:
	print "an Exception occured:"
	print e
        return "error loading data..."
    
    if history is None:
        history = {'error': 'no data available'}
    
    out = {'computenode': cn, 'data': history}
    return json.dumps(out)

'''deprecated'''
@app.route('/history')
def history():
    history = []
    a = {}
    with  open(historyFile, 'rb') as f:
        while True:
            try:
                data = pickle.load(f)
                history.append(data)
	    except EOFError:
                break
    a = history.pop(0)
    index = 1
    for o in history:
       dictMerge(a, o, index)
       index += 1
    return render_template('history.html', history=a)

'''
REST routes for static data
'''
@app.route('/static/snapshots')
def static_snapshots():
	global cnSnapshots
	entries = []
	for k in sorted(cnSnapshots):
		out = computecn.computeData(cnSnapshots[k])
		entries.append(out)
	return json.dumps(entries)

@app.route('/static_computenodes')
def static_computenodes():
    global cnSnapshots
    out = []
    for k in sorted(cnSnapshots):
        c = cnSnapshots[k]
        entries = {'cpu': computecn.computeDetailCPU(c),
            'memory': computecn.computeDetailMemory(c),
            'network': computecn.computeDetailNetwork(c),
            'power': computecn.computeDetailPower(c),
            'filesystem': computecn.computeDetailFilesystem(c),
            'storage': computecn.computeDetailStorage(c)}
        try: 
            entries.append({'meta': computecn.computeDetailMeta(c)})
        except:
            pass
        out.append({'computenode': k, 'data': entries})
    return json.dumps(out)

@app.route('/static_computenode<id>')
def static_computenode(id):
    global cnSnapshots
    global vmSnapshots
    vms = []
    c = cnSnapshots['computenode'+id]
    entries = {'cpu': computecn.computeDetailCPU(c),
        'memory': computecn.computeDetailMemory(c),
        'network': computecn.computeDetailNetwork(c),
        'power': computecn.computeDetailPower(c),
        'filesystem': computecn.computeDetailFilesystem(c),
        'storage': computecn.computeDetailStorage(c)}
    try: 
        entries.append({'meta': computecn.computeDetailMeta(c)})
    except:
        pass
    vm = computevm.computeVMData(c, vmSnapshots)
    out = {'computenode': c.name, 'data': entries, 'vms': vm}
    return json.dumps(out)

@app.route('/static_virtualmachines')
def static_virtualmaschines():
	global vmSnapshots
	vms = computevm.renderVM(vmSnapshots)
	return json.dumps(vms)

@app.route('/static_virtualmachine/<id>')
def static_snVMs(id):
	entries = []
        vm = computevm.renderSingleVM(id)
        return json.dumps(vm) 

'''
REST routes for Angular calls
'''
@app.route('/ajax')
def ajax():
    history = []
    a = {}
    with open(storagePath + 'history.p', 'rb') as f:
        while True:
            try:
                data = pickle.load(f)
                history.append(data)
	    except EOFError:
                break
    f.close()
    
    #a = history.pop(0)
    #for o in history:
    #   dictMerge(a, o)
    #return json.dumps(a)
    index = 1
    a = history.pop(0)
    for o in history:
       dictMerge(a, o, index) 
       index += 1
    handleNulls(a)
    return json.dumps(a)    

@app.route('/computenodes')
def cnAjax():
    global cnSnapshots
    cnList = []
    for c in cnSnapshots:
        # only read runnning compute nodes 
        if (cnSnapshots[c].meta['meta:state'] == 'running'):
            hist = []
            b = {}
            fname = storagePath + c + '.p'
            with open(fname, 'rb') as fc:
                while True:
                    try:
                        data = pickle.load(fc)
                        hist.append(data)
                    except EOFError:
                        fc.close()
                        break
            b = hist.pop(0)
	    index = 1
            for o in hist:
                dictMerge(b, o, index)
		index += 1
            cnList.append({'computenode': c, 'data' : b})
    return json.dumps(sorted(cnList))

@app.route('/computenode<id>')
def singleCNAjax(id):
    shist = []
    sb = {}
    fname = storagePath + 'computenode' + id + '.p'
    with open(fname, 'rb') as sfc:
        while True:
            try:
                data = pickle.load(sfc)
                shist.append(data)
            except EOFError:
                sfc.close()
                break
    sb = shist.pop(0)
    index = 1
    for o in shist:
        dictMerge(sb, o, index)
	index += 1
    return json.dumps({'computenode': 'computenode'+id,
                        'data': sb})

@app.route('/virtual')
def vmAjax():
    global vmSnapshots
    vmList = []
    for vm in sorted(vmSnapshots):
        try:
            vmObject = vmSnapshots[vm]
            if (vmObject.meta['meta:vm_state'] == 'running'):
                vmhist = []
                vmb = {}
                fname = storagePath + vm + '.p'
                with open(fname, 'rb') as vmf:
                    while True:
                        try:
                            data = pickle.load(vmf)
                            vmhist.append(data)
                        except EOFError:
                            vmf.close()
                            break
                vmb = vmhist.pop(0)
		index = 1
                for o in vmhist:
                    dictMerge(vmb, o, index)
		    index += 1
                # vmList.append({'virtualmashine': vm, 'status': vmObject.meta['meta:vm_state'], 'data': vmb})
                vmList.append({'virtualmachine': vm, 'data': vmb})
        except Exception as ex:
            # print "error reading vmhistory"
            # print ex
            pass
    return json.dumps(vmList)

@app.route('/virtual/<id>')
def singleVMAjax(id):
    global vmSnapshots
    try:
        vm = vmSnapshots[id]
    except:
        abort(404)

    svmhist = []
    svmb = {}
    fname = storagePath + id + '.p'
    with open(fname, 'rb') as svmf:
        while True:
            try:
                data = pickle.load(svmf)
                svmhist.append(data)
            except EOFError:
                svmf.close()
                break
    svmb = svmhist.pop(0)
    index = 1
    for o in svmhist:
        dictMerge(svmb, o, index)
	index += 1
    return json.dumps({'virtualmashine': id,
                        'status': vmSnapshots[id].meta['meta:vm_state'],
                        'data': svmb})

@app.route('/virtual/computenode<id>')
def computenodeVM(id):
    global cnSnapshots
    global vmSnapshots
    c = cnSnapshots['computenode'+id]
    amount = len([[k ,v] for k, v in c.vms.items() if re.search('^vms:vm_uuid.[0-9][0-9]?', k)])
    vmList = []
    for i in range(amount):
        vmName = c.vms['vms:vm_uuid.'+str(i)]
        try:
            vmObject = vmSnapshots[vmName]
            vmhist = []
            vmb = {}
            fname = storagePath + vmName + '.p'
            with open(fname, 'rb') as vmf:
                while True:
                    try:
                        data = pickle.load(vmf)
                        vmhist.append(data)
                    except EOFError:
                        vmf.close()
                        break
            vmb = vmhist.pop(0)
	    index = 1
            for o in vmhist:
                dictMerge(vmb, o, index)
		index += 1
            # vmList.append({'virtualmashine': vmName, 'status': vmObject.meta['meta:vm_state'], 'data': vmb})
            vmList.append({'virtualmachine': vmName, 'data': vmb})
        except Exception as ex:
            # print "error reading vmhistory"
            # print ex
            pass
    return json.dumps(vmList)

'''
merges overview list recusive
'''
'''
def dictMerge(a, o):
 for k, v in o.iteritems():
    if (k in a and isinstance(a[k], dict) and isinstance(o[k], collections.Mapping)):
         dictMerge(a[k], o[k])
    else:
        if not k in a or not isinstance(a[k], list):
		if k in a:
			a[k] = [round(a[k], 2), round(o[k], 2)]
		else:
			a[k] = [float(0), round(o[k], 2)]
        else:
                a[k].append(round(o[k], 2))
'''

def dictMerge(all, toAdd, iteration):
    # iterate over elements in toAdd and append them to all
    for key in toAdd:
        addElementToDict(all, key, toAdd[key], iteration)

def addElementToDict(all, key, value, iteration):
    # this key is known already and it is a dict
    if key in all:
        if isinstance(all[key], dict):
            if isinstance(value, collections.Mapping):
                dictMerge(all[key], value, iteration)
            else:
                raise ValueError("unhandled case 1")
        elif isinstance(all[key], list):
            # handle gap by nulling intermediate elements.
	    if len(all[key]) <= iteration:
	    	for index in range(len(all[key]), iteration):
			if not index in all:
				all[index].append(None)
            all[key].append(round(value, 2))
        else: # all[key] is something completely different
	    # put the value in a list!
	    all[key] = [round(all[key], 2), round(value, 2)]
    if not key in all:
        if isinstance(value, collections.Mapping):
            all[key] = Dict()
            dictMerge(all[key], value, iteration)
        elif isinstance(value, double):
            # this is supposed to be a list
            all[key] = [None]*(iteration) 
            all[key].append(round(value, 2))
        else:
            raise ValueError("unhandled case 3")

def handleNulls(mydict):
    for key in mydict:
	value = mydict[key]
        if isinstance(value, dict):
            handleNulls(value)
        elif isinstance(value, list):
            allNull = True
	    # fill at the end if not 60 items in list
            for index in range(len(value), 60):
		if not index in value:
			value.append(None)
	    # detect empty metrics
	    for index in range(0, 60):
                if value[index] != None:
                    allNull = False
		    break;
            if allNull == True:
		mydict.pop(key, None)
        else:
            raise ValueError("unhandled case: value is of type %s" % type(value) )

def checkConnection():
    hostname = cfg['servers']['thrift']
    port = cfg['servers']['thriftport']
    response = os.system("ping -c 1 " + hostname)
    print response
    if response == 0:
        print hostname + ' is up'
        return True
    else:
        print hostname + ' is down'
        return False

if __name__ == "__main__":
    print "start app via flask directly"
    # run mainloop for Snapshots
    thread.start_new_thread(worker.mainloop, ())
    # app.debug = True
    app.run(host=host, port=port, threaded=True)
