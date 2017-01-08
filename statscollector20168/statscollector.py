
from bottle import route, run
from json import dumps
from requestmanager import *
from myGlobal import myGlobal
import json
import os.path
from tcshow import *
@route('/hello')
def hello():
    return "Hello World!"

#switch_list = ["10.0.0.1:9999","10.0.0.2:9998","10.0.0.3:9997"]
e = threading.Event()

@route("/stats/<start_ip>/<end_ip>/<earliest_idx>/<num_entries>",method='GET')
def get_path_stats(start_ip, end_ip,earliest_idx,num_entries):
   '''
   This function is the main Northbound API 
   '''
   global e
   link_capacity = find_link_cap(start_ip,end_ip)
   path = find_path(start_ip, end_ip)
   #print path
   start_monitor(e)
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
   #print "a3"
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
   # rate1_X, rate1_Y = generateAveragedRateXY(qos_stats, 1, 2)
   # rate2_X, rate2_Y = generateAveragedRateXY(qos_stats, 1, 3)
   # import matplotlib.pyplot as plt
   # fig = plt.figure()
   # ax1 = fig.add_subplot(211)
   # ax1.plot(rate1_X, rate1_Y, 'r')
   # ax1.plot(rate2_X, rate2_Y, 'b')

   # nVideo_X, nVideo_Y = generateNumOfFlowXY(qos_stats, 1, -2)
   # nData_X, nData_Y = generateNumOfFlowXY(qos_stats, 1, -1)
   # ax2 = fig.add_subplot(212)
   # ax2.plot(nVideo_X, nVideo_Y, 'r')
   # ax2.plot(nData_X, nData_Y, 'b')
   # plt.savefig('result.png')


   return result 

def generateDetailedRateXY(content,index_X,index_Y):
   x_axis = []
   y_axis = []
   cumulative_time = 0.0
   x_axis.append(cumulative_time)
   rate= 0.0
   prev_byte = float(content[0][index_Y])
   y_axis.append(rate)
   for i in range(len(content)):
         if i != 0:
            # cal time
            delta_time = float(content[i][index_X])
            cumulative_time = cumulative_time+float(delta_time)
            # cal rate
            curr_byte = float(content[i][index_Y])
            rate = (curr_byte - prev_byte)*8/delta_time/1024
            prev_byte = curr_byte
            x_axis.append(cumulative_time)
            y_axis.append(rate)
   return x_axis, y_axis

def generateAveragedRateXY(content,index_X,index_Y):
        x_axis = []
        y_axis = []
        cumulative_time = 0.0
        x_axis.append(cumulative_time)
        rate= 0.0
        prev_total_byte = float(content[0][index_Y])
        y_axis.append(rate)
        interval = 1 # set a interval that you want to average out
        end_time = interval #
        for i in range(len(content)):
            if i != 0:
                     # cal time
               delta_time = float(content[i][index_X])
               cumulative_time = cumulative_time+float(delta_time)
               if cumulative_time < end_time:
                  pass
               else:
                  curr_total_byte = float(content[i][index_Y])
                  rate = (curr_total_byte-prev_total_byte)*8/interval/1024/1024  #Mbps
                  prev_total_byte = curr_total_byte
                  x_axis.append(end_time)
                  y_axis.append(rate)
                  end_time = end_time+interval
        return x_axis, y_axis


def generateNumOfFlowXY(content, index_X, index_Y):
         x_axis = []
         y_axis = []
         cumulative_time = 0.0
         x_axis.append(cumulative_time)
         #rate= 0.0
         init_flows = float(content[0][index_Y])
         y_axis.append(init_flows)
         for i in range(len(content)):
                if i != 0:
                        # cal time
                        delta_time = float(content[i][index_X])
                                # cal rate
                        cumulative_time = cumulative_time+float(delta_time)
                        num_of_flows = float(content[i][index_Y])
         #print num_of_flows
                        x_axis.append(cumulative_time)
                        y_axis.append(num_of_flows)
         return x_axis, y_axis





# rate1_X, rate1_Y = generateRateXY(content, 1, 2)
# rate2_X, rate2_Y = generateRateXY(content, 1, 3)
# plt.plot(rate1_X, rate1_Y, 'r')
# plt.plot(rate2_X, rate2_Y, 'b')
# plt.show()

def find_link_cap(start_ip,end_ip):
   if start_ip == "10.0.0.2":
      retVal = [10,15]#[10Mbps,15Mbps]
      return retVal
   if end_ip == "10.0.0.2":
      retVal = [10,15]
      return retVal

def find_path(start_ip,end_ip):
   if start_ip == "10.0.0.2":
      retVal = ["s1-eth2","s2-eth1","s3-eth2"] # the first two are the relevant switches, the last one is were to get the delay
      return retVal
   if end_ip == "10.0.0.2":
      retVal = ["s2-eth2","s1-eth1","s4-eth2"] # the first two are the relevant switches, the last one is were to get the delay
      return retVal
# STATICALLY DEFINE LINKS IN HERE.
if __name__ == '__main__':
   # qosmonitor(e)
   run(server='cherrypy',host='10.0.0.254', port=8080, debug=True)
