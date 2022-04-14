#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : subdirectory auto umount fault case.
@Time : 2021/11/13 13:44
@Author : caoyi
"""
import pytest
from time import sleep
from common.cli import YrfsCli
from common.util import sshClient
from common.cluster import get_netcard_info, check_cluster_health
from config import consts
from depend.client import client_mount
from common.fault import makeFault

class CheckHealthException(Exception):
    pass

class Test_umountFault(YrfsCli):
    def setup_class(self):
        self.testdir = "autotest_umount_fault"
        self.mountdir = consts.MOUNT_DIR
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)

    def teardown_class(self):
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def setup(self):
        # 创建测试目录
        self.sshserver.ssh_exec("cd %s&& mkdir %s" % (self.mountdir, self.testdir))
        self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, "*", "rw"))
        # 客户端挂载
        mountstat = client_mount(self.clientip, self.testdir)
        assert mountstat == 0, "Expect client mount success."

    @pytest.mark.parametrize("tc", ("loss","delay"))
    def test_network_delay(self, tc):
        """
        3128 集群网络延迟较高时，触发子目录自动卸载
        3129 集群网络丢包时，触发子目录自动卸载
        """
        tc_add = ""
        tc_del = ""
        try:
            net_info = get_netcard_info()
            hosts = [i[1][1] for i in net_info.values()]
            nets = [i[0] for i in list(net_info.values())[0]]
            seg = ""
            for net in nets:
                if tc_add:
                    seg = ";"
                if tc == "delay":
                    tc_add = tc_add + seg + "tc qdisc add dev %s root netem delay 100ms" % net
                else:
                    tc_add = tc_add + seg + "tc qdisc add dev %s root netem loss 0%%" % net
                tc_del = tc_del + seg + "tc qdisc del dev %s root" % net
            # 设置网络延迟
            for host in hosts:
                sshserver = sshClient(host)
                sshserver.ssh_exec(tc_add)
                sshserver.close_connect()
            #目录删除
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
            stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountdir)
            assert stat != 0, "Expect umount success."
            self.sshclient.ssh_exec("df -h > /dev/null 2>&1")
            stat, _ = self.sshclient.ssh_exec("cat /etc/mtab|grep " + self.mountdir)
            assert stat != 0, "Expect umount success."

        finally:
            for host in hosts:
                sshserver = sshClient(host)
                sshserver.ssh_exec(tc_del)
                sshserver.close_connect()
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, "*"))

    @pytest.mark.parametrize("fault_type", ("reboot","stop"))
    def test_reboot_mgr(self, fault_type):
        """
        3130 stop mgmt主服务，立即触发子目录自动卸载
        """
        makefault = makeFault()
        #故障测试
        try:
            if fault_type == "reboot":
                makefault.reboot_mgr(crash_cmd="reboot -f",check=False)
            else:
                makefault.kill_mgr(check=False)
            sleep(5)
            # 目录删除
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
            stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountdir)
            sleep(1)
            #assert stat != 0, "Expect umount success."
            self.sshclient.ssh_exec("df -h > /dev/null 2>&1")
            stat, _ = self.sshclient.ssh_exec("cat /etc/mtab|grep " + self.mountdir)
            assert stat != 0, "Expect umount success."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, "*"))
            sleep(10)
            checkstat = check_cluster_health()
            if checkstat != 0:
                CheckHealthException("Cluster rebuild Failed")