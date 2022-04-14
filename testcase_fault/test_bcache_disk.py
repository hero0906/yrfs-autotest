#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : bcache disk fault test suite
@Time : 2021/11/03 19:02
@Author : caoyi
"""
import os
import pytest
import time
from time import sleep
from common.cli import YrfsCli
from common.util import sshClient
from common.cluster import check_cluster_health
from config import consts
from depend.client import client_mount, run_vdbench

@pytest.mark.faultTest
class Test_Bcache(YrfsCli):

    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.testdir = "autotest_bcache_fault_" + time.strftime("%m-%d-%H%M%S")
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        sshserver = sshClient(self.serverip)
        # 检查是否为bcache环境
        bcache_stat, _ = sshserver.ssh_exec("lsblk|grep bcache")
        assert bcache_stat == 0, "not bcache env"
        # 磁盘信息获取
        _, backend_disks = sshserver.ssh_exec("ls /sys/fs/bcache/*-*/bdev* -al|awk -F \"/\" '{print $19}'")
        self.backend_disks = backend_disks.split()
        _, self.cache_disk = sshserver.ssh_exec("ls /sys/fs/bcache/*-*/cache0* -al|awk -F \"/\" '{print $19}'")
        _, self.cset_uuid = sshserver.ssh_exec("ls /sys/fs/bcache/|grep -")
        self.oss_service_name = self.get_cli(self, "oss_service")
        # 客户端挂载
        sshserver.ssh_exec("mkdir -p " + self.testpath)
        mount_stat = client_mount(self.clientip, acl_add=True)
        assert mount_stat == 0, "client mount failed."
        sshserver.close_connect()

    def teardown_class(self):
        sshserver = sshClient(self.serverip)
        sshserver.ssh_exec("rm -fr " + self.testpath)
        sshserver.close_connect()

    def setup(self):
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
    def teardown(self):
        self.sshclient.close_connect()
        self.sshserver.close_connect()

    def test_remove_ssd(self):
        """
        1912 	3	校验writeback模式下，拔掉ssd，IO是否报错
        """
        # 客户端运行vdbench业务
        try:
            vdstat = run_vdbench(self.testpath)
            assert vdstat == 0, "vdbench run failed."
            # 移除一个块ssd缓存盘
            down_stat, _ = self.sshserver.ssh_exec("echo offline >/sys/block/{0}/device/state&&echo 1 \
                            >/sys/block/{0}/device/delete".format(self.cache_disk))
            assert down_stat == 0, "down disk failed."
            sleep(10)
            # 检查业务没有运行失败
            vd_stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench|grep -v grep > /dev/null 2>&1")
            assert vd_stat == 0, "vdbench run failed"
            # 停止vdbench业务
            self.sshclient.ssh_exec("killall -9 java")
        finally:
            # 重新上线磁盘
            self.sshserver.ssh_exec("echo \"- - -\" > /sys/class/scsi_host/host0/scan")
            sleep(20)
            # 环境修复
            self.sshserver.ssh_exec("systemctl stop " + self.oss_service_name)
            # bcache修复
            self.sshserver.ssh_exec("umount /data/oss*")
            # 磁盘repair
            _, new_cache = self.sshserver.ssh_exec("cat /proc/partitions |grep sd|tail -n 1|awk '{print $4}'")
            self.sshserver.ssh_exec("echo /dev/{0} > /sys/fs/bcache/register".format(new_cache))
            for disk in self.backend_disks:
                self.sshserver.ssh_exec("echo /dev/{0} > /sys/fs/bcache/register".format(disk))
            # 注册bcache盘
            for i in range(2):
                _, new_bcaches = self.sshserver.ssh_exec("cat /proc/partitions |grep bcache|awk '{print $4}'")
                for disk in new_bcaches.split():
                    # self.sshserver.ssh_exec("umount /dev/" + disk)
                    self.sshserver.ssh_exec("xfs_repair -L /dev/%s > /dev/null 2>&1" % disk)
            # 有可能会attach失败，多执行一次以防万一。
            self.sshserver.ssh_exec("echo /dev/{0} > /sys/fs/bcache/register".format(new_cache))
            for disk in self.backend_disks:
                self.sshserver.ssh_exec("echo {1} > /sys/block/{0}/bcache/attach".format(disk, self.cset_uuid))
            # 重新挂载数据盘
            self.sshserver.ssh_exec("mount -a")
            # 启动服务
            start, _ = self.sshserver.ssh_exec("systemctl start " + self.oss_service_name)
            assert start == 0, "oss service start failed."
            # 检测集群是否恢复正常
            check_cluster_health()
        # 恢复后io正常
        vdstat = run_vdbench(self.testpath)
        assert vdstat == 0, "vdbench run failed."
        sleep(30)
        vd_stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench|grep -v grep > /dev/null 2>&1")
        assert vd_stat == 0, "vdbench run failed"

    def test_remove_hdd(self):
        """
        1913 	3	校验writeback模式下，拔掉hdd，IO是否报错
        """
        try:
            # 客户端运行vdbench业务
            vdstat = run_vdbench(self.testpath)
            assert vdstat == 0, "vdbench run failed."
            # 移除一块hdd磁盘
            choice_disk = self.backend_disks[0]
            down_stat, _ = self.sshserver.ssh_exec("echo offline >/sys/block/{0}/device/state;echo 1"
                                                   ">/sys/block/{0}/device/delete".format(choice_disk))
            sleep(10)
            # 检查业务没有运行失败
            vd_stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench|grep -v grep > /dev/null 2>&1")
            assert vd_stat == 0, "vdbench run failed"
            # 停止vdbench业务
            self.sshclient.ssh_exec("killall -9 java")
        finally:
            # 重新上线磁盘
            self.sshserver.ssh_exec("echo \"- - -\" > /sys/class/scsi_host/host0/scan")
            sleep(20)
            # 环境修复
            _, new_disk = self.sshserver.ssh_exec("cat /proc/partitions |grep sd|tail -n 1|awk '{print $4}'")
            self.sshserver.ssh_exec("systemctl stop " + self.oss_service_name)
            self.sshserver.ssh_exec("umount /data/oss*")
            # backend_disks.append(new_disk)
            # bcache修
            self.sshserver.ssh_exec("echo /dev/{0} > /sys/fs/bcache/register;echo {1} > \
                /sys/block/{0}/bcache/attach".format(new_disk, self.cset_uuid))
            _, new_bcaches = self.sshserver.ssh_exec("cat /proc/partitions |grep bcache|tail -n 1|awk '{print $4}'")
            for i in range(2):
                self.sshserver.ssh_exec("xfs_repair -L /dev/%s > /dev/null 2>&1" % new_bcaches)
            self.sshserver.ssh_exec("echo /dev/{0} > /sys/fs/bcache/register;echo {1} > \
                /sys/block/{0}/bcache/attach".format(new_disk, self.cset_uuid))
            # 重新挂载数据盘
            self.sshserver.ssh_exec("mount -a")
            # 启动服务
            self.sshserver.ssh_exec("systemctl start " + self.oss_service_name)
            # 检测集群是否恢复正常
            check_cluster_health()
        # 恢复后io正常
        vdstat = run_vdbench(self.testpath)
        assert vdstat == 0, "vdbench run failed."
        sleep(30)
        vd_stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench|grep -v grep > /dev/null 2>&1")
        assert vd_stat == 0, "vdbench run failed"
