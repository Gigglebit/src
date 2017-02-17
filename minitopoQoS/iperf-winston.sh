sleep 15 && iperf3 -c 10.0.0.3 -p 5001 -t 60 -i 1 -w 16m &
sleep 30 && iperf3 -c 10.0.0.3 -p 5002 -t 10 -i 1 -w 16m &
sleep 45 && sudo kill $(pgrep -f \"iperf -c 10.0.0.3 -p 5002\") &