#!/bin/bash

rate=$1Mbit
rate2=$2Mbit
rate3=$3Mbit
# rateb=5Mbit

function add_qdisc {
    dev=$1
    tc qdisc del dev $dev root
    echo qdisc removed

    tc qdisc add dev $dev root handle 1: htb default 1
    echo qdisc added

    tc class add dev $dev classid 1:1 parent 1: htb rate $rate ceil $rate
    tc class add dev $dev classid 1:10 parent 1:1 htb rate $rate2 ceil $rate
#    tc class add dev $dev classid 1:11 parent 1:1 htb ceil $rate
    tc class add dev $dev classid 1:11 parent 1:1 htb rate $rate3 ceil $rate
    echo classes created

    tc qdisc add dev $dev parent 1:10 handle 10: netem delay 1us limit 50
    tc qdisc add dev $dev parent 1:11 handle 11: netem delay 1us limit 100
    echo queue specified
    # Direct iperf traffic to classid 10:1
    #tc filter add dev $dev parent 1: protocol ip prio 1 u32 match ip dst 10.0.0.2/32 match ip dport 8000 0xffff flowid 1:10
    #tc filter add dev $dev parent 1: protocol ip prio 1 u32 match ip src 10.0.0.2/32 match ip sport 8000 0xffff flowid 1:10
    tc filter add dev $dev parent 1: protocol ip prio 1 u32 match ip dst 10.0.0.2/32 flowid 1:10
    tc filter add dev $dev parent 1: protocol ip prio 1 u32 match ip src 10.0.0.2/32 flowid 1:10
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 1 0xff flowid 1:11
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 6 0xff flowid 1:11
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 17 0xff flowid 1:11
    echo filters added
}

function add_delay {
    dev=$1
    delay=$2
    tc qdisc del dev $dev root
    echo add_delay qdisc removed
    tc qdisc add dev $dev root handle 1: htb default 1
    # #tc qdisc add dev $dev root handle 1:0 netem delay $delay
    echo root created
    tc class add dev $dev classid 1:1 parent 1: htb rate $rate ceil $rate
    tc class add dev $dev classid 1:12 parent 1:1 htb rate $rate ceil $rate
    # tc class add dev $dev classid 1:11 parent 1:1 htb rate $rate3 ceil $rate
    echo classes created
    tc qdisc add dev $dev parent 1:12 handle 12: netem delay $delay
    # tc qdisc add dev $dev parent 1:11 handle 11: netem delay $delay limit 1000
    # echo queue specified
    # Direct iperf traffic to classid 10:1
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 1 0xff flowid 1:12
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 6 0xff flowid 1:12
    tc filter add dev $dev protocol ip parent 1: prio 1 u32 match ip protocol 17 0xff flowid 1:12
    #tc qdisc add dev $dev root handle 1:0 tbf burst 2kb limit 2kb mtu 1514 rate $rateb
    echo add_delay created
    


}

# add_qdisc s1-eth1
add_qdisc s1-eth2
# add_qdisc s2-eth1
add_qdisc s2-eth2
# add_qdisc s2-eth3
add_delay s3-eth2 50ms
add_delay s4-eth2 50ms
add_delay s3-eth1 1us
add_delay s4-eth1 1us
