#!/bin/bash
echo "start monitor experiment"
sudo sysctl -w net.ipv4.tcp_congestion_control=reno
sudo python minitopo.py --exp exp1 \
     	   		--btnSpeed 5 \
			--hs_bw 10 \
			--delay 50000 \
			--maxq 100 \
			--intf2 eth3 \

echo "cleaning up..."
sudo killall -9 iperf ping
sudo mn -c > /dev/null 2>&1
echo "end"
