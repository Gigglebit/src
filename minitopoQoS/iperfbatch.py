from subprocess import Popen
from itertools import islice

raw_command = 'sleep %s; iperf -c 10.0.0.3 -p %s -t %s -i 1 -w 16m -Z reno > iperf-%s.txt'
commands = []
length = 14
for i in xrange(length):
    tmp = raw_command %(i,5001+i,(length-i)*1, 5001+i)
    commands.append(tmp)
    print tmp


# commands = [
#     'sleep 5; iperf -c 10.0.0.3 -p 5001 -t 30 -i 1 -w 16m -Z reno > iperf-5001.txt',
#     'sleep 5; iperf -c 10.0.0.3 -p 5001 -t 30 -i 1 -w 16m -Z reno > iperf-5001.txt',
#     'date; df -h; sleep 3; date',
#     'date; hostname; sleep 2; date',
#     'date; uname -a; date',
# ]

# generate_commands 

max_workers = 14  # no more than 2 concurrent processes
processes = (Popen(cmd, shell=True) for cmd in commands)
running_processes = list(islice(processes, max_workers))  # start new processes
while running_processes:
    for i, process in enumerate(running_processes):
        if process.poll() is not None:  # the process has finished
            running_processes[i] = next(processes, None)  # start new process
            if running_processes[i] is None: # no new processes
                del running_processes[i]
                break