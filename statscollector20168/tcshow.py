#!/bin/python
import os,re
import time
import subprocess
import threading
import Queue
from myGlobal import myGlobal
from netaddr import IPNetwork, IPAddress
from copy import deepcopy
#from threading import *
############################
# This is a simple function for extracting useful info from tc -s qdisc show
# entries[]:
# Extracted columns include:
# 0 1 2 3 4 5 6 7 8 9
# idx RootNo. DevName Sent(Bytes) Sent(Packets) Dropped(Packets) Overlimits(Bytes) Requeues Backlog(Bytes) Backlog(Packets)
#
# Because linux tc may also show the child queue class, Parent, Queue Depth and Propagation Delay may also be considered
#
# RootNo is related to multiple Queues of an interface pls ignore at the current stage
#
############################
#Length of the stats collector moving window: maximaly holding 100 entries
MAX_BUF = 100

#This is the dict that holds all entries
tc_dict ={}

#Dictionary possible keys
entry_keys = ['RootNo','Dev','SentB','SentP','DroppedP','OverlimitsB','Requeues','BackB','BackP']

#Child queue possible keys
netem_keys = ['RootNo','Dev','Parent','Q_Depth','P_Delay','SentB','SentP','DroppedP','OverlimitsB','Requeues','BackB','BackP']

#Available interfaces (devices), e.g. eth1, eth0
#dev_keys = []

#Available child interfaces (devices)
#netem_dev_keys = []

#Time tracker
prev_t = 0
curr_t = 0
delta_t = 0
prev_flows = {}
recorded_bni = 0
prev_bni = 0
matches_d2 = []
last_min_rate = 4 #initialise the min rate
q = Queue.Queue() # min-rate pass from qos to tcshow
#qab = Queue.Queue() #number of a flow and b flow
summaryq = Queue.Queue() #summaryq to be saved and plot
nflow_dict={'nVideo':0, 'nData':0}
recorded_queued_bytes = 0
prev_long1 = 2.5
prev_short1 = 2.5
# bniq = Queue.Queue() #bandwidth of non-interactive flows
def tcshow (e):
    '''
    This function handles a pulling event received from the timer
    It wakes up every 50ms (sampling time),collect all the data of all interfaces
    and store them in tc_dict
    '''
    # wait until being waken up
    e.wait()
    e.clear()
    
    # grab the locker and idx
    tclock = myGlobal.tclock
    idx = myGlobal.idx
    summarylock = myGlobal.summarylock
    # qoslock = myGlobal.qoslock
    # bnilock = myGlobal.bnilock
    # calculate delta_t
    global curr_t
    global prev_t
    global delta_t
    global matches_d2
    global q
    #global qab
    global nflow_dict
    global recorded_bni
    global last_min_rate
    global prev_bni
    global recorded_queued_bytes
    global prev_long1
    global prev_short1
    entry = []
    curr_t =time.time()
    delta_t = curr_t-prev_t
    prev_t = curr_t
    
    #Available interfaces (devices), e.g. eth1, eth0
    dev_keys = []
    #Available child interfaces (devices)
    netem_dev_keys = []
    
    #parse tc show root result
    tccmd = "tc -s qdisc show"
    result = subprocess.check_output(tccmd,shell=True)
    parse_result = re.compile(r'qdisc\s*[a-zA-Z_]+\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sroot\s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\dA-Z]+)b+\s([\d]+)p')
    matches_d = parse_result.findall(result)
    entry = [dict(zip(entry_keys,row)) for row in matches_d]
    #parse tc show parent result
    result2 = subprocess.check_output(tccmd,shell=True)
    #print result2
    parse_result2 = re.compile(r'qdisc\snetem\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sparent\s([0-9]+:[0-9]+)\slimit\s([0-9]+)\sdelay\s([0-9.]+)[mu]s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\dA-Z]+)b\s([\d]+)p')
    matches_d2 = parse_result2.findall(result2)

    netem_entry = [dict(zip(netem_keys,row)) for row in matches_d2]
    #print matches_d2
    #save everything into a tc_dict{idx:{dev1:{'RootNo':...},dev2:{'RootNo':...}}}
    visited = {}
    SentB_10 = 0
    BackB_10 = 0

    nflow = deepcopy(nflow_dict)
    # qoslock.acquire()
    # while not qab.empty():
    #     nflow = qab.get()
    # qoslock.release()   
    for item in entry:
        #print item
        # qoslock.acquire()
        for netem_item in netem_entry:
            if netem_item['Dev']==item['Dev'] and item['Dev'] not in visited:
                item.update({'P_Delay':netem_item['P_Delay']})
                t = netem_item['BackB']
                if t.endswith('K'):
                    t = t[0:len(t)-1] + "000"
                if t.endswith('M'):
                    t = t[0:len(t)-1] + "000000"
                item.update({'BackB':t}) 
                if netem_item['RootNo']=='10':
                        SentB_10 = netem_item['SentB']
                        BackB_10 = t
                        item.update({'SentB':SentB_10})
                        item.update({'SentP':netem_item['SentP']})
                        item.update({'BackP':netem_item['BackP']})
                        item.update({'RootNo':'10'})
                        # qoslock.acquire()
                        # if q.empty():
                        #     item.update({'MinRate':last_min_rate})
                        # else:
                        #     while not q.empty():
                        # last_min_rate = q.get()
                        item.update({'MinRate':last_min_rate})
                        # qoslock.release() 
                        visited[item['Dev']]=True
            if netem_item['Dev']==item['Dev'] and netem_item['Dev']=='s1-eth2' and netem_item['RootNo'] == '11':
                summary = [] #curr_t, delta_t, sentB(video), sentB(non-video), backloggedPackets(video), backloggedPackets(non-video),num of video, num of non-video flows
                summary.append(curr_t)
                summary.append(delta_t)
                summary.append(SentB_10)
                summary.append(netem_item['SentB'])
                summary.append(prev_long1)
                summary.append(prev_short1)
                summary.append(BackB_10)
                t = netem_item['BackB']
                if t.endswith('K'):
                    t = t[0:len(t)-1] + "000"
                if t.endswith('M'):
                    t = t[0:len(t)-1] + "000000"
                summary.append(t)
                # bnilock.acquire()
                recorded_bni = (float(netem_item['SentB'])-float(prev_bni))*8/delta_t/1000/1000
                t = netem_item['BackB']
                if t.endswith('K'):
                    t = t[0:len(t)-1] + "000"
                if t.endswith('M'):
                    t = t[0:len(t)-1] + "000000"
                recorded_queued_bytes = int(t)
                # bniq.put(bni)
                prev_bni = netem_item['SentB']
                # bnilock.release()
                if 'nVideo' in nflow:
                    summary.append(nflow['nVideo'])
                    summary.append(nflow['nData'])     
                summarylock.acquire()
                summaryq.put(summary)
                print '------------------summary!!!!------------------'
                print summary
                summarylock.release()
            
            #     while not q.empty():
            #         nflow = qab.get()
            #         print '----------------nflownflownflow!!!!!@!#!#$@$$349689387698970--------------------'

            #         if 'nVideo' in nflow:
            #             print "it is here!!!!!!!!!!!!!!!!!!!!&*(&(*&(*&(*&(*&*&%!#%^@%#^@%!^*$^@%"
            #             with open(netem_item['Dev']+'.txt', 'a') as the_file:
            #                 print "it is here!!!!!!!!!!!!!!!!!!!!&*(&(*&(*&(*&(*&*&%!#%^@%#^@%!^*$^@%"
            #                 the_file.write("%s, %s, %s, %s, %s, %s, %s, %s\n" % (curr_t, delta_t, SentB_10, netem_item['SentB'], BackP_10, netem_item['BackP'],nflow['nVideo'],nflow['nData']))

        item.update({'delta_t': delta_t})
        dev_keys.append(item['Dev'])
    #     print item
    # print '---------tcdict item-----------'
    
    #lock tc_dict and update it
    tclock.acquire()
    tc_dict.update({idx : dict(zip(dev_keys,entry))})
    # print tc_dict[idx]['s1-eth2']
    if len(tc_dict) > MAX_BUF:
	#remove the out of boundary entry
        del tc_dict[idx-MAX_BUF]
    idx +=1
    myGlobal.idx=idx
    tclock.release()





def flowsMetaData(flows, outPort):
    nLowDelay = 0.0
    nNonLow = 0.0
    for flow in flows:
        # if (outPort == flow['outPort']):
            # print flow
            if(flow[4]): 
                nLowDelay = nLowDelay + 1
            else:
                nNonLow = nNonLow + 1
    #print nLowDelay, nNonLow
    # if (nLowDelay+nNonLow!=0):
    #     ratio = nLowDelay/(nLowDelay+nNonLow)
    # else : 
    #     ratio = 0.0
    ratio = (nLowDelay+1)/(nLowDelay+nNonLow+2)
    return ratio, nLowDelay, nNonLow 

def changeQdisc(linkCap, ratio, intfs, nLowDelay, bni, queued_bytes):
    rate1 = 0.001
    global prev_long1
    global prev_short1
    alphaL = 0.02
    alphaS = 0.1
    print "The ratio of no. of low delay/no. of total is: "+str(ratio)
    # if ratio < 0.2 :
    #     rate1 = linkCap*0.2
    # elif ratio > 0.99 :
    #     rate1 = linkCap*0.99
    # else: 
    #     rate1 = linkCap*ratio

    longterm=(1-alphaL)*prev_long1+alphaL*linkCap*ratio
    shorterm=0
    margin = 0.1*linkCap
    # if linkCap-bni-margin > prev_short1:
    #     shorterm = linkCap - bni - margin
    # else:
    qflag = (queued_bytes!=0)  
    #shorterm = (1-alphaS)*prev_short1+alphaS*max(linkCap-bni-margin,prev_long1)
    shorterm = (1-alphaS)*prev_short1+alphaS*(prev_long1 if qflag else linkCap-margin)
    rate1 = shorterm
    if rate1 == 0:
        rate1 = 0.001*linkCap
    rate2 = linkCap - rate1
    #print ratio
    #rate2 = 0.001*linkCap
    print ("now the min rate for low delay queue is %s", rate1)
    print ("now the min rate for data queue is %s", rate2)
    cmd = 'bash tc_change_diff2.sh %s %s %s ' % (linkCap,rate1,rate2)
    #cmd = 'bash tc_change_diff2.sh %s %s %s ' % (10,9.999,0.001)
    prev_long1 = longterm
    prev_short1 = shorterm
    #global q
    global last_min_rate
    # if nLowDelay!=0:
    #     q.put(rate1/nLowDelay)
    # else:
    last_min_rate = rate1
    #q.put(rate1)
    #print intfs
    for intf in intfs.keys():
        cmd = cmd + intf +" "
    print cmd
    os.system(cmd)

def findPortMinMax(portRange):
    portMinMax = portRange.split('-')
    portMin = 0
    portMax = 0
    if len(portMinMax) == 2:
        portMin = int(portMinMax[0])
        portMax = int(portMinMax[1])+1
    else :
        portMin = int(portMinMax[0])
        portMax = int(portMinMax[0])+1
    #print portMin,portMax
    return range(portMin, portMax)

def detectflows(intf, servIP, portRange, cToS):
    flows = []
    tccmd = "sudo ovs-ofctl dump-flows "+intf
    result = subprocess.check_output(tccmd,shell=True)
    portTrueRange = findPortMinMax(portRange)
    # print "-----------detect flows---------------"
    iperf_server='10.0.0.3'
    visited_server_port = []    
    for item in result.split('\n'):
        elem = item.split(',')
        #print elem
        #print len(elem)
        if len(elem)<=9:
            pass

        elif elem[8]=='udp' or 'tcp':
           #print '---------flows--------'
           #print elem
           #if int(elem[6].split('=')[1]) < 1:
               if (cToS):
                    servPort = elem[-1].split(' ')[0].split('=')[1]
                    # print "this server port and port range are"
                    # print servPort,portTrueRange
                    if IPAddress(elem[-4].split('=')[1]) in IPNetwork(servIP) and int(servPort) in portTrueRange and elem[8]=='udp':
                        if int(elem[6].split('=')[1]) < 2:
                            flow = {'serverIP':elem[-4].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-5].split('=')[1], 'clientPort':elem[-2].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':True}
                            flows.append(flow)
                            
                    else :
                        if IPAddress(elem[-5].split('=')[1]) in IPNetwork(iperf_server) and elem[8]=='tcp' and int(elem[6].split('=')[1]) < 5 and elem[-1].split(' ')[1].split(':')[1] =='2':
                            flow = {'serverIP':elem[-4].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-5].split('=')[1], 'clientPort':elem[-2].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':False}
                            flows.append(flow)
                            clientPort = elem[-1].split(' ')[0].split('=')[1] 
                            if clientPort not in visited_server_port:
                                visited_server_port.append(clientPort)
                                flows.append(flow)
                            #print flow      
               else:
                    servPort = elem[-2].split('=')[1]
                    # print "this server port and port range are"
                    # print servPort,portTrueRange

                    if (elem[-5].split('=')[0]=='dl_src'):
                        # print elem
                        continue

                    if IPAddress(elem[-5].split('=')[1]) in IPNetwork(servIP) and int(servPort) in portTrueRange and elem[8]=='udp':
                        if int(elem[6].split('=')[1]) < 2:
                            flow = {'serverIP':elem[-5].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-4].split('=')[1], 'clientPort':elem[-1].split(' ')[0].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':True}
                            flows.append(flow)
                    else :  
                        if IPAddress(elem[-4].split('=')[1]) in IPNetwork(iperf_server) and elem[8]=='tcp' and int(elem[6].split('=')[1]) < 5 and elem[-1].split(' ')[1].split(':')[1] =='2':    
                            flow = {'serverIP':elem[-5].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-4].split('=')[1], 'clientPort':elem[-1].split(' ')[0].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1],'outPort':elem[-1].split(' ')[1].split(':')[1], 'lowDelay':False}
                            clientPort = elem[-1].split(' ')[0].split('=')[1] 
                            if clientPort not in visited_server_port:
                                visited_server_port.append(clientPort)
                                flows.append(flow)
    # print flows
    # print "------------------finished detect flows---------------------"    
    return flows

def extractSwitchID(intf):
    switches = {}
    intfs = intf.split(',')
    intfs_dict = {}
    for item in intfs:
        #print item     
        port_dict = {}
        item_str = item.split('-')
        sw = item_str[0]
        port_dict['port']=item_str[1].split('eth')[1]
        intfs_dict[item]= port_dict
        if sw not in switches.keys():
            switches.setdefault(sw,[]).append(intfs_dict)
        else:
#           print intfs_dict
            if intfs_dict not in switches[sw]:
                switches.setdefault(sw,[]).append(intfs_dict)

    return switches
SchmittTrigger={}
qosTrigger = 'CLEAR'
value = {}
prev_nLow = 0
prev_nData = 0

def applyQdiscMgmt(intf, ipblock, portRange, cToS, linkCap):
    # e.wait()
    # e.clear()
    global recorded_bni

    bni = recorded_bni
    #print ("I am getting bni %s", bni)


    print "------------applyQdiscMgmt------------------"
    qoslock = myGlobal.qoslock
    global prev_flows
    global prev_nLow
    global prev_nData
    global SchmittTrigger
    global qosTrigger
    # global qab
    # global value 
    global recorded_queued_bytes
    print ("I am getting queued bytes %s", recorded_queued_bytes)
    switches = extractSwitchID(intf)
    for sw in switches.keys():
        flowList = []
        #detecting flows
        flows = detectflows(sw, ipblock, portRange, cToS) #
        #filter out flowLists
        # qoslock.acquire()
        for flow in flows:
            if flow['outPort'] =='2':
                if IPAddress(flow['serverIP']) not in IPNetwork(ipblock):
                    flowList.append([flow['serverIP'],flow['serverPort'],flow['clientIP'],flow['clientPort'],flow['lowDelay'],flow['outPort']])
                else:
                    # print "flow"
                    # print flow
                    if (flow['lowDelay']):
                        flowList.append([flow['serverIP'],flow['serverPort'],flow['clientIP'],flow['clientPort'],flow['lowDelay'],flow['outPort']])
        #key value pair                
        # for key, value in switches[sw][0].items():#for each port of a switch
        #     ratio, a,b = flowsMetaData(flowList ,value['port'])
        #     # print value['port']+':'

        #     print '--------the ratio, number of videos, number of data is shown below:----------'
        #     print ratio, a, b
        #     value['nVideo']=a
        #     value['nData']=b
        #     print value 
        #     qab.put(value)
        #     switches[sw][0][key] = value                    
        #print switches[sw][0] 
        print "--------------flowList-------------"         
        print flowList

        # as long as flowList changed
        if sw in prev_flows.keys():
            flowListString = ''.join(str(r) for v in flowList for r in v)
            if prev_flows[sw] == flowList:
                print "flows did not change since last time"
            else:
                qosTrigger= 'INIT'

            # value['nVideo'] =prev_nLow
            # value['nData'] = prev_nData

            # if qosTrigger=='INIT':
            #     SchmittTrigger[flowListString] = 0
            #     qosTrigger='WAIT'
            # elif qosTrigger == 'WAIT':
            #     SchmittTrigger[flowListString] += 1
            #     if SchmittTrigger[flowListString] >= 5:
            #         qosTrigger='CHANGE'
            # elif qosTrigger == 'CHANGE':
            ratio,nLow,nData = flowsMetaData(flowList, '2')
            # value['nVideo']=nLow
            # value['nData']=nData
            global nflow_dict
            nflow_dict['nVideo']=nLow
            nflow_dict['nData']=nData            
            switches[sw][0]['s1-eth2'] = value 
            changeQdisc(float(linkCap), ratio, switches[sw][0],nLow,recorded_bni,recorded_queued_bytes)
            print "flows have been changed"
            #     SchmittTrigger = {}
            #     qosTrigger ='CLEAR'
            # else:
            #     pass

            # qab.put(value)
            # prev_nLow = value['nVideo']
            # prev_nData = value['nData']
            prev_nLow = nflow_dict['nVideo']
            prev_nData = nflow_dict['nData']
        prev_flows[sw] = flowList   
        # qoslock.release()
    # result = tcQoS(switches[sw][0])
    # print "---------------tcQoS :%s------------" %sw
    # print result
    # print "------------------------------------"

# def tcQoS (intflist):
#     result=dict()
#     global matches_d2
#     global curr_t
#     global delta_t
#     for i in range(0,len(matches_d2),2):
#         for intf, values in intflist.items():
#             if intf==matches_d2[i][1]:
#                 result[intf] = "%s, %s, %s, %s, %s, %s, %s, %s\n" % (curr_t, delta_t, matches_d2[i][5],matches_d2[i+1][5],matches_d2[i][-1],matches_d2[i+1][-1],values['nVideo'],values['nData'])
#     return result

def qosmonitor(e):
    counter = 200
    t3 = QoSTimer(e,counter)
    t3.daemon = True
    t3.start()

class TControl(threading.Thread):
    '''
    A simple thread for controlling tcshow.
    This function is triggered by timer event
    '''
    def __init__(self,e,counter):
        super(TControl, self).__init__()
        self.keeprunning = counter
        self.initial = counter
        self.event = e
    def run(self):
        try:
            while self.keeprunning > 0:
                tcshow(self.event)
                intflist = 's1-eth2'
                #applyQdiscMgmt(intflist,'10.0.0.3/32','5001-5002','True','0.15')
                self.keeprunning-=1
        except KeyboardInterrupt:
            print "stoptimer"
            self.stop()
    def stop(self):         
        self.keeprunning = 0
    def reset(self):
        self.keeprunning = self.initial
        sleep = False


class QoSTimer(threading.Thread):
    '''
    A simple thread for controlling tcshow.
    This function is triggered by timer event
    '''
    def __init__(self,e,counter):
        super(QoSTimer, self).__init__()
        self.keeprunning = counter
        self.initial = counter
        self.event = e
    def run(self):
        try:
            while self.keeprunning > 0:
                self.event.wait()
                intflist = 's1-eth2'
                #linkcap = 0.5
                #time.sleep(0.05)
                applyQdiscMgmt(intflist,'10.0.0.2/32','8001-8100',False,'5')
                #self.keeprunning-=1

                #self.keeprunning-=1
        except KeyboardInterrupt:
            print "stoptimer"
            self.stop()
    def stop(self):         
        self.keeprunning = 0
    def reset(self):
        self.keeprunning = self.initial
        sleep = False

if __name__ == '__main__':
    e = threading.Event()
    counter = 200
    t1 = TControl(e,counter)
    t2 = Timer1(e,0.05,counter)
    t1.daemon = True
    t1.start()
    t2.start()
