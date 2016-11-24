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
from mininet.node import Node,Controller,RemoteController,OVSKernelSwitch
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

#################################
def startNAT( root, inetIntf='eth0', subnet='10.0/8' ):
    """Start NAT/forwarding between Mininet and external network
root: node to access iptables from
inetIntf: interface for internet access
subnet: Mininet subnet (default 10.0/8)="""

    # Identify the interface connecting to the mininet network
    localIntf = root.defaultIntf()

    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Create default entries for unmatched traffic
    root.cmd( 'iptables -P INPUT ACCEPT' )
    root.cmd( 'iptables -P OUTPUT ACCEPT' )
    root.cmd( 'iptables -P FORWARD DROP' )

    # Configure NAT
    root.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
    root.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )

    # Instruct the kernel to perform forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=1' )

def stopNAT( root ):
    """Stop NAT/forwarding between Mininet and external network"""
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Instruct the kernel to stop forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=0' )

def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
by specifying manual configuration in /etc/network/interfaces
root: a node in the root namespace (for running commands)
intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if ( line ) not in config:
        print '*** Adding', line.strip(), 'to', cfile
        with open( cfile, 'a' ) as f:
            f.write( line )
    # Probably need to restart network-manager to be safe -
    # hopefully this won't disconnect you
    root.cmd( 'service network-manager restart' )

def connectToInternet( network,switch='s2', rootip='10.254', subnet='10.0/8'):
    """Connect the network to the internet
switch: switch to connect to root namespace
rootip: address for interface in root namespace
subnet: Mininet subnet"""
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]

    # Create a node in root namespace
    root = Node( 'root', inNamespace=False )

    # Prevent network-manager from interfering with our interface
    fixNetworkManager( root, 'root-eth0' )

    # Create link between root NS and switch
    link = network.addLink( root, switch)
#,bw=100,max_queue_size=500,use_htb=True)
    link.intf1.setIP( rootip, prefixLen )
    # Start network that now includes link to root namespace
    network.start()
    
    # Start NAT and establish forwarding
    startNAT( root )

    # Setting up DHCP
    print "IF 0 ROOT ->" + str(os.getuid())
    out = network.hosts[0].cmd('sudo dhcpd')
    print "DHCPD = " + out

# Establish routes from end hosts
    for host in network.hosts:
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'route add -net', subnet, 'dev', host.defaultIntf() )
        host.cmd( 'route add default gw', rootip )
    return root

def checkIntf( intf ):
    "Make sure intf exists and is not configured."
    if ( ' %s:' % intf ) not in quietRun( 'ip link show' ):
        error( 'Error:', intf, 'does not exist!\n' )
        exit( 1 )
    ips = re.findall( r'\d+\.\d+\.\d+\.\d+', quietRun( 'ifconfig ' + intf ) )
    if ips:
        error( 'Error:', intf, 'has an IP address,'
               'and is probably in use!\n' )
        exit( 1 )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    #if not switch:
        #switch = network[ 's1' ]  # switch to use
    #if not routes:
        #routes = [ '10.0.0.0/24' ]
    #connectToRootNS( network, switch, ip, routes )
    rootnode = connectToInternet( network )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print
    print "*** Hosts are running sshd at the following addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print
    print "*** Type 'exit' or control-D to shut down network"
#    CLI( network )
#    for host in network.hosts:
#        host.cmd( 'kill %' + cmd )
#    network.stop()
    return rootnode

def addRealIntf(net, intf, switch):

    intfName = intf
    info( '*** Connecting to hw intf: %s' % intfName )

    info( '*** Checking', intfName, '\n' )
    checkIntf( intfName )
    info( '*** Adding hardware interface', intfName, 'to switch',
          switch.name, '\n' )
    _intf = Intf( intfName, node=switch)
# ,bw=bw,max_queue_size=maxq)
    info( '*** Note: you may need to reconfigure the interfaces for '
         'the Mininet hosts:\n', net.hosts, '\n' )



