import matplotlib.pyplot as plt
# content = []
# with open('result.txt', 'r') as the_file:
#   content = the_file.readlines()
# print len(content)
import json
content = []
with open('result.json') as json_data:
    content = json.load(json_data)
    
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
            rate = (curr_byte - prev_byte)*8/delta_time/1000
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
                  rate = (curr_total_byte-prev_total_byte)*8/interval/1000/1000  #Mbps
                  prev_total_byte = curr_total_byte
                  x_axis.append(end_time)
                  y_axis.append(min(rate,10))
                  end_time = end_time+interval
        return x_axis, y_axis


def generateNumOfFlowXY(content, index_X, index_Y):
         x_axis = []
         y_axis = []
         cumulative_time = 0.0
         x_axis.append(cumulative_time)
         #rate= 0.0
         init_flows = float(content[1][index_Y])
         y_axis.append(init_flows)
         for i in range(len(content)):
                if i != 0 and i != 1:
                        # cal time
                        delta_time = float(content[i][index_X])
                                # cal rate
                        cumulative_time = cumulative_time+float(delta_time)
                        num_of_flows = float(content[i][index_Y])
         #print num_of_flows
                        x_axis.append(cumulative_time)
                        y_axis.append(num_of_flows)
         return x_axis, y_axis

rate1_X, rate1_Y = generateAveragedRateXY(content, 1, 2)
rate2_X, rate2_Y = generateAveragedRateXY(content, 1, 3)
# import matplotlib.pyplot as plt
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.plot(rate1_X, rate1_Y, 'r')
ax1.plot(rate2_X, rate2_Y, 'b')

#nVideo_X, nVideo_Y = generateNumOfFlowXY(content, 1, -2)
#nData_X, nData_Y = generateNumOfFlowXY(content, 1, -1)
nVideo_X, nVideo_Y = generateNumOfFlowXY(content, 1, -4)
nData_X, nData_Y = generateNumOfFlowXY(content, 1, -3)
ax2 = fig.add_subplot(212)
ax2.plot(nVideo_X, nVideo_Y, 'r')
ax2.plot(nData_X, nData_Y, 'b')
plt.savefig('result.png')