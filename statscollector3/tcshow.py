#!/bin/python
import os,re
import time
import subprocess
import threading
import Queue
from myGlobal import myGlobal
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
    
    # calculate delta_t
    global prev_t
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
    parse_result = re.compile(r'qdisc\s*[a-zA-Z_]+\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sroot\s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\d]+)b+\s([\d]+)p')
    matches_d = parse_result.findall(result)
    entry = [dict(zip(entry_keys,row)) for row in matches_d]
    #parse tc show parent result
    result2 = subprocess.check_output(tccmd,shell=True)
    #print result2
    parse_result2 = re.compile(r'qdisc\snetem\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sparent\s([0-9]+:[0-9]+)\slimit\s([0-9]+)\sdelay\s([0-9.]+)ms[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\dA-Z]+)b\s([\d]+)p')
    matches_d2 = parse_result2.findall(result2)
    netem_entry = [dict(zip(netem_keys,row)) for row in matches_d2]
    #print matches_d2
    #save everything into a tc_dict{idx:{dev1:{'RootNo':...},dev2:{'RootNo':...}}}
    for item in entry:
    	#print item
        for netem_item in netem_entry:
	    if netem_item['Dev']==item['Dev']:
                item.update({'P_Delay':netem_item['P_Delay']}) 
        item.update({'delta_t': delta_t})
        dev_keys.append(item['Dev'])
    
    #lock tc_dict and update it
    tclock.acquire()
    tc_dict.update({idx : dict(zip(dev_keys,entry))})
    #print tc_dict[idx]['s1-eth2']
    if len(tc_dict) > MAX_BUF:
	#remove the out of boundary entry
        del tc_dict[idx-MAX_BUF]
    idx +=1
    myGlobal.idx=idx
    tclock.release()



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
				self.keeprunning-=1
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
