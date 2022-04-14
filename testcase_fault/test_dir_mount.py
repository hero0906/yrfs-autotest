#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : subdirectory mount fault case.
@Time : 2021/11/13 13:44
@Author : caoyi
"""
import logging
from time import sleep
from common.fault import makeFault
from common.cluster import check_cluster_health
from common.util import sshClient
from config import consts
from depend.client import client_mount
from common.cli import YrfsCli

logger = logging.getLogger(__name__)


class Test_dirMountFault(YrfsCli):
    def setup_class(self):
        # 挂载客户端
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1
        self.mountpoint = consts.MOUNT_DIR

        # self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_add", "", "*", "rw"))
        # 执行客户端挂载
        mstat = client_mount(self.clientip, acl_add=True)
        assert mstat == 0, "Expect mount success."

    def setup(self):
        self.makefault = makeFault()
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)

    def teardown(self):
        # self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_del", "", "*"))
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_reboot_meta(self):
        """
        2042  reboot掉meta主节点，挂载点正常
        """
        # reboot meta
        testfile = "autotest_dir_fault_2042"
        self.makefault.reboot_meta(crash_cmd="reboot -f", check=False)
        # sleep 5s
        sleep(5)
        # 查看挂载点
        stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountpoint)
        assert stat == 0, "Expect df -h success."
        try:
            stat, _ = self.sshclient.ssh_exec("cd %s&&touch %s" % (self.mountpoint, testfile))
            assert stat == 0, "Expect touch success."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountpoint, testfile))
            sleep(10)
            check_cluster_health()

    def test_kill_meta(self):
        """
        2043 kill掉meta主节点，挂载点正常
        """
        testfile = "autotest_dir_fault_2042"
        self.makefault.kill_meta(check=False)
        sleep(5)
        stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountpoint)
        assert stat == 0, "Expect df -h success."
        try:
            stat, _ = self.sshclient.ssh_exec("cd %s&&touch %s" % (self.mountpoint, testfile))
            assert stat == 0, "Expect touch success."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountpoint, testfile))
            check_cluster_health()

    def test_reboot_oss(self):
        """
        2047 reboot掉storage主节点，挂载点正常
        """
        # reboot meta
        testfile = "autotest_dir_fault_2042"
        self.makefault.reboot_oss(crash_cmd="reboot -f", check=False)
        # sleep 5s
        sleep(5)
        # 查看挂载点
        stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountpoint)
        assert stat == 0, "Expect df -h success."
        try:
            stat, _ = self.sshclient.ssh_exec("cd %s&&touch %s" % (self.mountpoint, testfile))
            assert stat == 0, "Expect touch success."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountpoint, testfile))
            sleep(60)
            check_cluster_health()

    def test_kill_oss(self):
        """
        2048 kill掉storage主节点，挂载点正常
        """
        testfile = "autotest_dir_fault_2042"
        self.makefault.kill_oss(check=False)
        # sleep 5s
        sleep(5)
        # 查看挂载点
        stat, _ = self.sshclient.ssh_exec("df -h|grep " + self.mountpoint)
        assert stat == 0, "Expect df -h success."
        try:
            stat, _ = self.sshclient.ssh_exec("cd %s&&touch %s" % (self.mountpoint, testfile))
            assert stat == 0, "Expect touch success."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountpoint, testfile))
            check_cluster_health()