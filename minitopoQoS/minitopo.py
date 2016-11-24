#!/usr/bin/python

"""
"""
import re
import sys
import os

from mininet.log import setLogLevel, debug, info, error,lg
from mininet.net import Mininet
from mininet.link import Intf,TCIntf
from mininet.util import custom,quietRun,irange,dumpNodeConnections
from mininet.cli import CLI
from mininet.node import Node,OVSController,Controller,RemoteController,OVSKernelSwitch
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink

from subprocess import *
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
#from hwhw import *
from nathw import *
parser = ArgumentParser(description = "Pulling Stats Tests")

parser.add_argument('--exp', '-e',
                    dest="exp",
                    action="store",
                    help="Name of the Experiment",
                    required=True)

parser.add_argument('--btnSpeed', '-b',
                    dest="btn",
                    action="store",
                    help="Bottleneck link speed",
                    required=True)

parser.add_argument('--hs_bw', '-HS',
                    dest="hs_bw",
                    type=float,
                    action="store",
                    help="Bandwidth between hosts and switchs",
                    required=True)

parser.add_argument('--delay',
                    dest="delay",
                    type=float,
                    help="Delay in milliseconds of host links",
                    default=10)

parser.add_argument('--maxq',
                    dest="maxq",
                    action="store",
                    help="Max buffer size of network interface in packets",
                    default=1000)

parser.add_argument('--intf1',
                    dest="intf1",
                    type=str,
                    action="store",
                    help="Real Interface")

parser.add_argument('--intf2',
                    dest="intf2",
                    type=str,
                    action="store",
                    help="Real Interface")

args = parser.parse_args()

class SimpleTopo(Topo):

   def __init__(self, k=2):
       super(SimpleTopo, self).__init__()
       self.k = k
       dhcp = self.addHost('dhcp')
       s1 = self.addSwitch('s1')
       s2 = self.addSwitch('s2')
       s3 = self.addSwitch('s3')
       s4 = self.addSwitch('s4')
       #s5 = self.addSwitch('s5')
       h1 = self.addHost('h1')
       h2 = self.addHost('h2')

       # self.addLink( s1, h1, bw=int(args.hs_bw))
       # self.addLink( s2, h2, bw=int(args.hs_bw))

       # self.addLink( s1, s3, bw=int(args.btn), delay=1) # 1us in order to show the backlog num of bytes
       # self.addLink( s4, s2, bw=int(args.btn), delay=1) # 1us in order to show the backlog num of bytes

       # self.addLink( s3, s4, bw=int(args.btn),delay=int(args.delay))
       # self.addLink( dhcp, s2, bw=int(args.hs_bw))
       self.addLink( s1, h1)
       self.addLink( s2, h2)

       self.addLink( s1, s3) # 1us in order to show the backlog num of bytes
       self.addLink( s4, s2) # 1us in order to show the backlog num of bytes

       self.addLink( s3, s4)
       self.addLink( dhcp, s2)
       #self.addLink( s1, s5, bw=int(args.hs_bw))
       #self.addLink( s2, s5, bw=int(args.hs_bw))
       
topos = { 'mytopo': ( lambda: SimpleTopo() ) }

def ping_latency(net):
    "(Incomplete) verify link latency"
    h1 = net.getNodeByName('h1')
    h1.sendCmd('ping -c 2 10.0.0.3')
    result = h1.waitOutput()
    print "Ping result:"
    print result.strip()

def Test():
   "Create network and run simple performance test"
   topo = SimpleTopo(k=2)
   # net = Mininet(topo=topo,
   #               host=CPULimitedHost, link=TCLink)#, controller=RemoteController)

  # topo = StarTopo(n=args.n, bw_host=args.bw_host,
  #                 delay='%sms' % args.delay,
  #                 bw_net=args.bw_net, maxq=args.maxq, diff=args.diff)
   net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink,
                autoPinCpus=True)
   poxController = net.addController(name='pox0' ,
                               controller=RemoteController ,
                               ip='127.0.0.1',
                               port=6633)
   s1 = net.getNodeByName('s1')
   s2 = net.getNodeByName('s2')
   if args.intf1 is not None:
	   addRealIntf(net,args.intf1,s1)
   if args.intf2 is not None:
      addRealIntf(net,args.intf2,s2)
#   net.start()
   opts = '-D -o UseDNS=no -u0'

#' '.join( sys.argv[ 1: ] ) if len( sys.argv ) > 1 else (
   rootnode=sshd(net, opts=opts)
#   print "Dumping host connections"
   dumpNodeConnections(net.hosts)
   ping_latency(net) 
#   net.pingAll()
   h1 = net.getNodeByName('h1')
   h2 = net.getNodeByName('h2')
#   dhcp = net.getNodeByName('dhcp')
#   out = dhcp.cmd('sudo dhcpd')
#   print "DHCPD = "+ out
   #h1.cmd("bash tc_cmd_diff.sh h1-eth0")
   #h1.cmd("tc -s show dev h1-eth0")
   print "Differentiate Traffic Between iperf and wget"
   os.system("bash tc_diff.sh")
   #h1.cmd('cd ./http/; python2.7 ./webserver.py &')
   #h1.cmd('cd ../')
   h2.cmd('iperf -s -w 16m -p 5001 -i 1 > iperf-recv.txt &')   
   #h2.cmd('iperf -s -p 5001 -i 1 > iperf-recv_TCP.txt &')
   h2.cmd('iperf -s -p 5003 -u -i 1 > iperf-recv_UDP.txt &')
   #h2.cmd('iperf -s -p %s -i 1 > iperf_server_TCP.txt &' % 5001)
#               (CUSTOM_IPERF_PATH, 5001, args.dir))
   #monitoring the network
  #monitor = Process(target=monitor_qlen,
                      #args=("%s"%args.iface,float(args.sampleR),int(args.nQ), "%s_%s"% (args.exp,args.out)))   
       

   for host in net.hosts:
       #host.cmd('tc qdisc del dev %s-eth0 root'%host)              
       #host.cmd('tc qdisc add dev %s-eth0 root tbf rate 10Mbit latency 2s burst 15k mtu 1512'%host)              
       host.cmd('ethtool -K %s-eth0 tso off gso off ufo off'%host)
   #start mininet CLI
   CLI(net)
   #terminate
   for host in net.hosts:
       host.cmd('kill %'+ '/usr/sbin/sshd')
   os.system('killall -9 iperf' )
   net.hosts[0].cmd('killall -9 dhcpd')
   stopNAT(rootnode)
   net.stop()
   h1.cmd("sudo pkill -9 -f webserver.py")
   h2.cmd("rm -f index.html*")
   Popen("killall -9 cat", shell=True).wait()

if __name__ == '__main__':
   setLogLevel('info')
   Test()
