#!/bin/bash

rate=$1Mbit
rate1=$2Mbit
rate2=$3Mbit

function change_qdisc {
    dev=$1

    tc class change dev $dev classid 1:10 parent 1:1 htb rate $rate1 ceil $rate
    #tc class change dev $dev classid 1:11 parent 1:1 htb rate $rate2 ceil $rate
    echo classes changed
    echo $dev
    echo $rate
    echo $rate1
    echo $rate2

}

change_qdisc s1-eth2
# change_qdisc s2-eth1
