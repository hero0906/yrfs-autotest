#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.util import sshClient
from config import consts
from common.cluster import check_cluster_health

def check_client_tools():
    print("checking Client Stat-----")
    for host in  consts.CLIENT:
        #检查fio工具是否存在
        ssh = sshClient(host)
        try:
            #ifconfig检查
            ifstat, _ = ssh.ssh_exec("ifconfig > /dev/null 2>&1")
            if ifstat != 0:
                print("Client %s Not found [ifconfig]" % host)
                break
            #fio检查
            fiostat, _ = ssh.ssh_exec("fio --version")
            if fiostat != 0:
                print("Client %s Not found [FIO]" % host)
            #检查vdbench是否存在
            javastat, _ = ssh.ssh_exec("java -version > /dev/null 2>&1")
            if javastat != 0:
                print("Client %s Not found [JAVA]" % host)
            vdstat, _ = ssh.ssh_exec("/opt/vdbench547/vdbench -t > /dev/null 2>&1")
            if vdstat != 0:
                print("Client: %s path: [%s] not found vdbench" % (host, "/opt/vdbench547"))
            #mdtest检查
            mdstat, _ = ssh.ssh_exec("mdtest -t > /dev/null 2>&1")
            if mdstat != 0:
                print("Client %s not found [mdtest]" % host)
            #fstest检查
            fsstst, _ = ssh.ssh_exec("stat /opt/pjdfstest-yrfs")
            if fsstst != 0:
                print("Client %s not found [fstest]" % host)
            #killall工具检测
            killall, _ = ssh.ssh_exec("killall --version")
            if killall != 0:
                print("Client %s not found [killall]" % host)
        finally:
            ssh.close_connect()
    print("Check Over-----")

def check_cluster():
    print("Checking Cluster Stat-----")
    stat = check_cluster_health()
    if stat != 0:
        print("Cluster not health,please check.")
    print("Check Over-----")


check_client_tools()
check_cluster()