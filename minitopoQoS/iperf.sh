#!/bin/bash 
#qsize=$1
iperf -c 10.0.0.3 -p 5001 -t 3600 -i 1 -w 16m -Z reno > iperf-5001.txt &
sleep 10; iperf -c 10.0.0.3 -p 5002 -t 3600 -i 1 -w 16m -Z reno > iperf-5002.txt &
#iperf -c 10.0.0.2 -p 5002 -t 3600 -i 1 -w 16m -Z reno > iperf2.txt &
# iperf -c 10.0.0.3 -p 5003 -t 3600 -i 1 -u -b 5m &
echo started iperf

