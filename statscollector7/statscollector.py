from bottle import route, run
from json import dumps
from requestmanager import *
from myGlobal import myGlobal
import os.path
import json
from tcshow import *
@route('/hello')
def hello():
    return "Hello World!"

#switch_list = ["10.0.0.1:9999","10.0.0.2:9998","10.0.0.3:9997"]

@route("/stats/<start_ip>/<end_ip>/<earliest_idx>/<num_entries>",method='GET')
def get_path_stats(start_ip, end_ip,earliest_idx,num_entries):
   '''
   This function is the main Northbound API 
   '''
   link_capacity = find_link_cap(start_ip,end_ip)
   path = find_path(start_ip, end_ip)
   #print path
   start_monitor()
   #print "a1"
   jpip_stats = requestmanager(path,link_capacity,int(earliest_idx),int(num_entries))
   #print "a2"
   #fname="./test/newfile%d.txt"%int(myGlobal.idx-1)
   #if not os.path.isfile(fname):
	#print "haha"
   #file = open(fname, "a")
   #file.write("%s"%jpip_stats)
   #file.close()
   result = dumps(jpip_stats)
   print "I have been called"
   return result

@route("/stats/showqos", method='GET')
def get_qos():
   qos_stats = []
   # start_QoS()
   global summaryq
   summarylock = myGlobal.summarylock
   summarylock.acquire()
   while not summaryq.empty():
      qos_stats.append(summaryq.get())
   summarylock.release()
   # print qos_stats
   result = dumps(qos_stats)

   with open('result.json', 'w') as outfile:
       json.dump(qos_stats, outfile)      

   return result 

def find_link_cap(start_ip,end_ip):
   if start_ip == "10.0.0.2":
      retVal = [5,10]#[5Mbps,10Mbps]
      return retVal
   if end_ip == "10.0.0.2":
      retVal = [5,10]
      return retVal   
def find_path(start_ip,end_ip):
   if start_ip == "10.0.0.2":
      retVal = ["s1-eth2","s2-eth1","s3-eth2"] # the first two are the relevant switches, the last one is were to get the delay
      return retVal
   if end_ip == "10.0.0.2":
      retVal = ["s2-eth2","s1-eth1","s4-eth2"] # the first two are the relevant switches, the last one is were to get the delay
      return retVal
# STATICALLY DEFINE LINKS IN HERE.

run(server='cherrypy',host='10.0.0.254', port=8080, debug=True)
