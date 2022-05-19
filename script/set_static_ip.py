#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.util import sshClient


#配置静态ip
def set_ips(ip_prefix,ip_end):

    gateway = ".".join(ip_prefix.split(".")[:2]) + ".0.1"

    for i in ip_end:

        ip = ip_prefix + "." + str(i)
        ssh = sshClient(ip)
        #获取ip对应的的网卡名称
        _ , devicename = ssh.ssh_exec("ifconfig |grep -B 3 %s|awk -F \":\" 'NR==1{{print $1}}'" % ip)
        print("Static netcard name %s" % devicename)
        #获取netmask
        _, netmask = ssh.ssh_exec("ifconfig |grep %s|awk '{{print $4}}'" % ip)
        print("Netmask: %s" % netmask)
        net_file = "/etc/sysconfig/network-scripts/ifcfg-" + devicename

        config = ("DEVICE={0}\
        \nNAME={0}\
        \nONBOOT=yes\
        \nIPV6INIT=yes\
        \nBOOTPROTO=static\
        \nNM_CONTROLLED=no\
        \nIPADDR={1}\
        \nNETMASK={2}\
        \nGATEWAY={3}\
        \nDNS1=114.114.114.114").format(devicename,ip,netmask,gateway)

        print("set host: " + str(ip))
        net_conf = config.format(devicename,ip)

        print("Set static ip: %s to: %s" % (ip, devicename))
        ssh.ssh_exec("echo -e \"%s\" > %s" % (net_conf, net_file))

        #设置其他网卡不自动获取ip地址
        print("Set BOOTPROTO to none")
        ssh.ssh_exec("ls /etc/sysconfig/network-scripts/ifcfg-*|grep -vE \"lo|%s\"|xargs -I {{}} sed -i \
        's/BOOTPROTO.*/BOOTPROTO=none/g' {{}}" % devicename)
        #重启网络
        print("Restart network")
        ssh.ssh_exec("/etc/init.d/network restart")
        ssh.close_connect()
#set_ips(ip_prefix="192.168.12",ip_end=(161,162,163,164),netmask ="255.255.0.0",gateway="192.168.0.1",device_name="ens224")
#set_ips(ip_prefix="10.16.2", ip_end=(11,12,13,14))
set_ips(ip_prefix="192.168.96", ip_end=(111,112,113,114))
#set_ips(ip_prefix="192.168.13", ip_end=(211,212,213,214))
#set_ips(ip_prefix="192.168.13", ip_end=(201,202,203,208))
