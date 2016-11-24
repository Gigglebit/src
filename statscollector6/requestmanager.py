#!/bin/python
import os,re
import time
import subprocess
import threading
from tcshow import * 
from myGlobal import myGlobal
from myGlobal import round_sigfigs as rnd
#a monitor running indicator
monitor_run = False

#threads holder
threads = []

#a copy of tc_dict
tc_result = {}

def cal_bw_delay(entries_range,idx,path,link_cap,tc_result):
	'''
	This function calculates bw and delay for requested entries:
	      |<---requested entries range--->|
	------|-------------------------------|---->t
	    start                            idx
	And then it return a list of integrated available bandwidth and delay along the path
	for example,
	[1,0.0501,5,50] means [idx = 1, delta_t = 0.0501s, Available bandwidth=5Mbps(bottleneck), total delay = 50ms]
	total delay includes propagation delay as well as queueing delay.

	'''
	j2k_stats = []
	#print "index"
	#print idx
	#print "index-range"
	#print idx-entries_range

	for i in xrange(idx-entries_range,idx,1):
		#list of one entry
		l=[]
		#link counter which indicates the current link index in link_cap
		link_ct = 0
		if (i-1) in tc_result:
			l.append(i)
			j = path[0]
			l.append(rnd(float(tc_result[i][j]['delta_t']),3))
			l.append(len(path) - 1) #the last switch is used for delay
			for j in path[0:2]: #ignore the last entry
				l.append(int(tc_result[i][j]['BackB']))
				l.append(int(tc_result[i][j]['SentB']) - int(tc_result[i-1][j]['SentB']))
				l.append(float(link_cap[link_ct]))
				if j == path[0] and 'P_Delay' in tc_result[i][path[2]]:
					l.append(rnd(float(tc_result[i][path[2]]['P_Delay']), 3))
				else:
					l.append(rnd(float(0), 3))
				link_ct+=1
			j2k_stats.append(l)
		else:
			pass
	#print j2k_stats
        #print entries_range 
	return j2k_stats

def resolve_idx(path,earliest_idx,num_entries,link_cap,idx,tc_result):
	'''
	The logic of the combination of earliest_idx and num_entries
	'''
	if num_entries >= MAX_BUF or num_entries >= idx or earliest_idx > idx or num_entries < 0 or earliest_idx < 0:
		#if anything is outbound return nothing
		return [" "] 	

	if num_entries==0 and earliest_idx ==0: #if none of the earlist_idx and num_entries were specified 
		if idx-MAX_BUF>=0: #when the index is higher more than 100
			return cal_bw_delay(MAX_BUF-1,idx,path,link_cap,tc_result) #calculate with all available data			
		else:
			return cal_bw_delay(idx,idx,path,link_cap,tc_result)
	elif num_entries!=0 and earliest_idx ==0: #if num_entries is specified
		if idx-MAX_BUF>=0:
			return cal_bw_delay(num_entries,idx,path,link_cap,tc_result) #calculate with the last num_entries entries 
		else:
			return cal_bw_delay(num_entries,idx,path,link_cap,tc_result)
	elif num_entries==0 and earliest_idx !=0: #if earlist idx is specified
		if idx-MAX_BUF>=0:
			if earliest_idx < idx-MAX_BUF:
				return cal_bw_delay(MAX_BUF-1,idx,path,link_cap,tc_result)
			else:
				return cal_bw_delay(idx-earliest_idx,idx,path,link_cap,tc_result)
		else:
			return cal_bw_delay(idx-earliest_idx,idx,path,link_cap,tc_result) #calculate with data starting earliest_idx
	else: #if you specified both of them
		if idx-MAX_BUF>=0: 
			if idx-num_entries < earliest_idx:
				return cal_bw_delay(idx-earliest_idx,idx,path,link_cap,tc_result)
			else:
				return cal_bw_delay(num_entries,idx,path,link_cap,tc_result)
		else:
			if idx-num_entries < earliest_idx:
				return cal_bw_delay(idx-earliest_idx,idx,path,link_cap,tc_result)
			else:
				return cal_bw_delay(num_entries,idx,path,link_cap,tc_result)

def requestmanager(path,link_cap,earliest_idx,num_entries):

	#print myGlobal.idx
	if len(tc_dict)>0:

		tclock = myGlobal.tclock
		tclock.acquire()
		tc_result = tc_dict
		index = myGlobal.idx-1
		tclock.release()		
		l = resolve_idx(path,earliest_idx,num_entries,link_cap,index,tc_result)
		return l
	else:
		return [" "]

class Timer1(threading.Thread):
	def __init__(self,e,seconds,counter):
		super(Timer1, self).__init__()
		self.runTime = seconds
		self.keeprunning = counter
		self.initial = counter
		self.event = e
	def run(self):
		try:
			counter = 0
			while self.keeprunning > 0:
				self.event.set()
				time.sleep(self.runTime)
				if counter == 20:
					#print self.keeprunning/20
					counter = 0
				counter +=1
				self.keeprunning-=1
				

			print "Going to sleep"
			global monitor_run
			monitor_run = False
		except KeyboardInterrupt:
			print "stoptimer"
			self.stop()
	def stop(self):			
		self.keeprunning = 0
	def reset(self):
		self.keeprunning = self.initial
		sleep = False

def start_monitor():
	'''
	create a thread for timer2 
	'''
	global monitor_run
	if not monitor_run:
		if len(threads)!=0:
			del threads[:]	
		e = threading.Event()
		counter = 200
		t1 = TControl(e,counter)
		t1.setName('TControl')
		t2 = Timer1(e,0.05,counter)
		t2.setName('Timer1')
		t1.daemon = True
		threads.append(t1)
		threads.append(t2)
		t1.start()
		t2.start()
		monitor_run = True
	else:
		#print "----reset threads-----"
	 	#print threads
		threads[0].reset()
		threads[1].reset()


if __name__ == '__main__':
	e = threading.Event()
	counter = 200
	t1 = TControl(e,counter)
	t2 = Timer1(e,0.05,counter)
	t1.start()
	t2.start()
	path = ["eth0","eth1"]
	earliest_idx = 0
	num_entries = 0
	tc_request(path)
