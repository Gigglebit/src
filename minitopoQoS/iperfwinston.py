from subprocess import Popen
from itertools import islice
import time
def run_iperf(num,duration,sleep):
	raw_command = 'sleep %s; iperf3 -c 10.0.0.3 -p %s -t %s -i 1 -w 16m > iperf-%s.txt'
	commands = []
	length = num
	#for i in xrange(length):
		#    tmp = raw_command %(0,5001+i,3*length-i*3, 5001+i)
    	#	tmp = raw_command %(sleep,5001+i,duration,5001+i)
    	#	commands.append(tmp)
    	#	print tmp
	tmp = raw_command %(0,5001+0,60,5001+0)
	commands.append(tmp)
	# tmp = raw_command %(0,5001+1,60,5001+1)
	# commands.append(tmp)
	tmp = raw_command %(20,5001+2,40,5001+2)
	commands.append(tmp)
	# tmp = raw_command %(20,5001+3,40,5001+3)
	# commands.append(tmp)
	tmp = raw_command %(40,5001+4,20,5001+4)
	commands.append(tmp)
	# tmp = raw_command %(40,5001+5,20,5001+5)
	# commands.append(tmp)

# commands = [
#     'sleep 5; iperf -c 10.0.0.3 -p 5001 -t 30 -i 1 -w 16m -Z reno > iperf-5001.txt',
#     'sleep 5; iperf -c 10.0.0.3 -p 5001 -t 30 -i 1 -w 16m -Z reno > iperf-5001.txt',
#     'date; df -h; sleep 3; date',
#     'date; hostname; sleep 2; date',
#     'date; uname -a; date',
# ]

# generate_commands 

	max_workers = num  # no more than 2 concurrent processes
	processes = (Popen(cmd, shell=True) for cmd in commands)
	running_processes = list(islice(processes, max_workers))  # start new processes
	while running_processes:
    		for i, process in enumerate(running_processes):
        		if process.poll() is not None:  # the process has finished
            			running_processes[i] = next(processes, None)  # start new process
            			if running_processes[i] is None: # no new processes
                			del running_processes[i]
                			break

#time.sleep(20)
run_iperf(3,60,0)
#run_iperf(1,20,0)
#run_iperf(3,20,0)
