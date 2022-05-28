#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : dir mount test suite
@Time : 2021/11/10 14:55
@Author : caoyi
"""

import pytest
from time import sleep
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount


@pytest.mark.funcTest
class Test_dirMount(YrfsCli):
    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        self.add_acl = self.get_cli(self, "acl_ip_add")
        self.del_acl = self.get_cli(self, "acl_ip_del")
        self.ipv6_cidr = "::/0"

    def teardown_class(self):
        self.sshclient.close_connect()
        self.sshserver.close_connect()

    def test_default_dir_mount(self):
        """
        1993 client端挂载子目录，mounts.conf配置中mount path不填默认挂载根目录
        """
        stat = client_mount(self.clientip, "", acl_add = True)
        assert stat == 0,"client mount failed."

    #@pytest.mark.skip
    def test_no_mount_point(self):
        """
        1994 client端挂载子目录，mounts.conf配置中mount point缺失导致挂载失败
        """
        stat = client_mount(self.clientip, mountpoint="", acl_add=True)
        assert stat != 0, "Client mount success."

    def test_no_cfg(self):
        """
        1995 client端挂载子目录，mounts.conf配置中cfg缺失导致挂载失败
        """
        try:
            client_mount(self.clientip, acl_add=True)
            self.sshclient.ssh_exec('echo "/mnt/yrfs /" > %s' % consts.CLIENT_MOUNT_FILE)
            self.sshserver.ssh_exec(self.add_acl.format("", self.ipv6_cidr, "rw"))
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            #重新启动
            stat = self.sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            assert stat != 0, "Client mount success."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format("", self.ipv6_cidr))

    def test_mount_diff_dir(self):
        """
        1996 client端挂载子目录，mounts.conf配置中没有添加的目录，挂载失败
        """
        #创建测试目录
        try:
            self.sshserver.ssh_exec("mkdir %s/autotest_mount_dir{1..2}" % consts.MOUNT_DIR)
            #设置dir1acl权限
            stat, _ = self.sshserver.ssh_exec(self.add_acl.format("autotest_mount_dir1", self.ipv6_cidr, "rw"))
            assert stat == 0, "set acl failed."
            #挂载子目录
            mountstat = client_mount(self.clientip, "autotest_mount_dir2")
            assert mountstat != 0, "dir mount failed."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format("autotest_mount_dir1", self.ipv6_cidr))
            self.sshserver.ssh_exec("rm -fr %s/autotest_mount_dir{1..2}" % consts.MOUNT_DIR)

    def test_rename_mountpoint(self):
        """
        1997 client端可以重命名挂载目录
        """
        try:
            client_mount(self.clientip, acl_add=True)
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            #重命名目录
            self.sshclient.ssh_exec("mv /mnt/yrfs /mnt/autotest_yrfs")
            stat = client_mount(self.clientip, mountpoint="/mnt/autotest_yrfs", acl_add=True)
            assert stat == 0, "Client mount failed."
        finally:
            self.sshclient.ssh_exec("umount -l /mnt/autotest_yrfs;rm -fr /mnt/autotest_yrfs")

    @pytest.mark.parametrize("mode", ("rw", "ro"))
    def test_mount_diff_dir(self, mode):
        """
        2017 同一个挂载点挂载到同一个client端不同目录，设置读写权限
        """
        testdir = "autotest_mount_dir_2017"
        testpath = consts.MOUNT_DIR + "/" + testdir
        #设置acl
        try:
            self.sshserver.ssh_exec("mkdir -p " + testpath)
            self.sshserver.ssh_exec(self.add_acl.format(testdir, self.ipv6_cidr, mode))
            #客户端挂载挂载
            client_mount(self.clientip, testdir)
            #停止客户端服务
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            #加入新的挂载点
            self.sshclient.ssh_exec('echo "/mnt/yrfs1 /etc/yrfs/yrfs-client.conf %s" >> %s' % (testdir, consts.CLIENT_MOUNT_FILE))
            #启动客户端挂载
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            #验证挂载正确
            stat, _ = self.sshclient.ssh_exec("findmnt %s &&findmnt /mnt/yrfs1" % (consts.MOUNT_DIR))
            assert stat == 0, "mount failed."
            t1, _ = self.sshclient.ssh_exec("touch %s/file1" % consts.MOUNT_DIR)
            t2, _ = self.sshclient.ssh_exec("touch /mnt/yrfs1/file2")
            if mode == "rw":
                assert t1 == 0, "touch failed."
                assert t2 == 0, "touch failed."
            else:
                assert t1 != 0, "touch success."
                assert t2 != 0, "touch success."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(testdir, self.ipv6_cidr))
            self.sshserver.ssh_exec("rm -fr " + testpath)

    @pytest.mark.parametrize("mode1, mode2", (("rw", "rw"),("rw","ro"),("ro","ro")))
    def test_diff_dir_diff_acl(self, mode1, mode2):
        """
        2024 不同挂载点挂载到同一个client端不同目录，设置不同权限
        """
        try:
            self.sshserver.ssh_exec("mkdir %s/autotest_mount_dir{1..2}" % consts.MOUNT_DIR)
            #设置权限
            self.sshserver.ssh_exec(self.add_acl.format("autotest_mount_dir1", self.ipv6_cidr, mode1))
            self.sshserver.ssh_exec(self.add_acl.format("autotest_mount_dir2", self.ipv6_cidr, mode2))
            #客户端挂载
            client_mount(self.clientip, "autotest_mount_dir1")
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            self.sshclient.ssh_exec(
                'echo "/mnt/yrfs1 /etc/yrfs/yrfs-client.conf autotest_mount_dir2" >> %s' % (consts.CLIENT_MOUNT_FILE))
            #重新启动
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            stat, _ =  self.sshclient.ssh_exec("findmnt %s &&findmnt /mnt/yrfs1" % (consts.MOUNT_DIR))
            assert stat == 0, "mount failed."
            #验证权限正确性
            t1, _ = self.sshclient.ssh_exec("touch %s/file1" % consts.MOUNT_DIR)
            t2, _ = self.sshclient.ssh_exec("touch /mnt/yrfs1/file2")
            if mode1 == "rw":
                assert t1 == 0, "touch failed."
            else:
                assert t1 != 0, "touch success."
            if mode2 == "rw":
                assert t1 == 0, "touch failed."
            else:
                assert t2 != 0, "touch success"
        finally:
            self.sshserver.ssh_exec(self.del_acl.format("autotest_mount_dir1", self.ipv6_cidr))
            self.sshserver.ssh_exec(self.del_acl.format("autotest_mount_dir2", self.ipv6_cidr))
            self.sshserver.ssh_exec("rm -fr %s/autotest_mount_dir{1..2}" % consts.MOUNT_DIR)

    def test_two_tier(self):
        """
        2033 父子目录同时挂载时，父目录删除已挂载子目录，子目录下读写操作失败
        """
        testdir = "autotest_acl_2033"
        subdir = testdir + "/dir1"
        mountdir = consts.MOUNT_DIR
        try:
            #创建测试目录
            self.sshserver.ssh_exec("cd %s&&mkdir -p %s" % (mountdir, subdir))
            #添加acl
            self.sshserver.ssh_exec(self.add_acl.format(testdir, self.ipv6_cidr, "rw"))
            self.sshserver.ssh_exec(self.add_acl.format(subdir, self.ipv6_cidr, "rw"))
            #目录挂载
            client_mount(self.clientip, testdir)
            #添加子目录
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            self.sshclient.ssh_exec('echo "/mnt/yrfs1 /etc/yrfs/yrfs-client.conf %s" >> %s' \
                                    % (subdir, consts.CLIENT_MOUNT_FILE))
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            sleep(2)
            #删除子目录
            self.sshclient.ssh_exec("cd %s&&rm -fr dir1" % mountdir)
            #检验目录是否挂载
            stat, _ = self.sshclient.ssh_exec("touch /mnt/yrfs1/file1")
            assert stat != 0,"Expect touch failed."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(testdir, self.ipv6_cidr))
            self.sshserver.ssh_exec(self.del_acl.format(subdir, self.ipv6_cidr))
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))

    @pytest.mark.parametrize("serveracl", ["rw", "ro"])
    @pytest.mark.parametrize("clientacl", ["rw", "ro"])
    def test_server_client(self, serveracl, clientacl):
        """
        2034 存储端设置权限读写，clinet端设置只读权限，验证子目录权限只读
        2035 （自动化）存储端设置权限只读，clinet端设置读写权限，验证子目录权限只读
        2036 （自动化）存储端设置权限只读，clinet端设置只读权限，验证子目录权限只读
        2037 （自动化）存储端设置权限读写，clinet端设置读写权限，验证子目录权限读写
        """
        testdir = "autotest_acl_2034"
        mountdir = consts.MOUNT_DIR
        try:
            #创建测试目录
            self.sshserver.ssh_exec("cd %s&&mkdir -p %s" % (mountdir, testdir))
            #权限设置
            self.sshserver.ssh_exec(self.add_acl.format(testdir, self.ipv6_cidr, serveracl))
            #客户端挂载
            client_mount(self.clientip, testdir, mode=clientacl)
            #验证权限是否符合预期
            stat, _ = self.sshclient.ssh_exec("touch %s/file1" % mountdir)
            if serveracl == "ro":
                assert stat != 0, "Excect touch failed."
            elif serveracl == "rw" and clientacl == "ro":
                assert stat != 0, "Excect touch failed."
            else:
                assert stat == 0, "Excect touch success."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(testdir, self.ipv6_cidr))
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))

    def test_mv_dir(self):
        """
        2039 存储端对子目录mv到其他目录，挂载点失效
        """
        testdir = "autotest_acl_2039"
        subdir = testdir + "/dir1"
        mountdir = consts.MOUNT_DIR
        try:
            self.sshserver.ssh_exec("cd %s&&mkdir -p %s" % (mountdir, subdir))
            #权限设置
            self.sshserver.ssh_exec(self.add_acl.format(subdir, self.ipv6_cidr, "rw"))
            #挂载
            client_mount(self.clientip, subdir)
            #删除子目录
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, subdir))
            #挂载点验证
            mstat, _ = self.sshclient.ssh_exec("df -h|grep " + mountdir)
            assert mstat != 0, "Excect umount success."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(subdir, self.ipv6_cidr))
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))
