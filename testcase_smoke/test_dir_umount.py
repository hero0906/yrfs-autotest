# coding=utf-8
"""
@Description : subdir auto unmount function test case
@Time : 2021/1/18 18:58
@Author : cay
"""

import pytest
import os
import logging
from time import sleep
from config import consts
from depend.client import client_mount
from common.util import sshClient
from common.cli import YrfsCli
from common.cluster import get_client_storageip

logger = logging.getLogger(__name__)


@pytest.mark.smokeTest
class Test_subdirUnmount(YrfsCli):

    def setup_class(self):

        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        self.testdir = "autotest_subdir_unmount"
        self.MOUNT_DIR = consts.MOUNT_DIR

        self.client_storageip = get_client_storageip(self.clientip)

        self.acl_ip_add = self.get_cli(self, "acl_ip_add", self.testdir, self.client_storageip, "rw")
        self.acl_ip_del = self.get_cli(self, "acl_ip_del", self.testdir, self.client_storageip)

    def teardown_class(self):
        self.sshclient.close_connect()
        self.sshserver.close_connect()

    def setup(self):
        self.sshserver.ssh_exec("mkdir -p %s" % (os.path.join(self.MOUNT_DIR, self.testdir)))
        self.sshserver.ssh_exec(self.acl_ip_add)

        mount_stat = client_mount(self.clientip, self.testdir)
        if mount_stat != 0:
            self.sshserver.ssh_exec(self.acl_ip_del)
            logger.error("client mount faild test will skip")
            pytest.skip(pytest.skip(msg="skip beause client mount failed", allow_module_level=True))
        sleep(1)

    def teardown(self):
        sleep(2)
        self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
        self.sshserver.ssh_exec(self.acl_ip_del)

    def test_remove_subdir(self):
        """
        caseID: 3132 删除子目录，客户端df 自动卸载挂载目录
        """
        self.sshserver.ssh_exec("rm -fr %s" % (os.path.join(self.MOUNT_DIR, self.testdir)))
        self.sshclient.ssh_exec("df -h")
        stat, _ = self.sshclient.ssh_exec("findmnt %s" % self.MOUNT_DIR)
        assert stat != 0, "subdir auto unmount failed!"

    def test_rename_subdir(self):
        """
        caseID: 3124 子目录改名后，客户端执行df命令，可以触发自动卸载
        """
        testpath1 = os.path.join(self.MOUNT_DIR, self.testdir)
        testpath2 = testpath1 + "02"

        self.sshserver.ssh_exec("mv %s %s" % (testpath1, testpath2))
        sleep(2)
        self.sshclient.ssh_exec("df -h")
        stat, _ = self.sshclient.ssh_exec("findmnt %s" % self.MOUNT_DIR)

        self.sshserver.ssh_exec("rm -fr %s" % testpath2)

        assert stat != 0, "subdir auto unmount failed!"

    def test_mv_subdir(self):
        """
        casetID: 3125 子目录mv到其他路径后，客户端执行df 命令，可以触发自动卸载
        """
        testpath1 = os.path.join(self.MOUNT_DIR, self.testdir)
        testpath2 = testpath1 + "02/"

        self.sshserver.ssh_exec("mkdir %s" % testpath2)
        self.sshserver.ssh_exec("mv %s %s" % (testpath1, testpath2))
        self.sshclient.ssh_exec("df -h")
        stat, _ = self.sshclient.ssh_exec("findmnt %s" % self.MOUNT_DIR)

        self.sshserver.ssh_exec("rm -fr %s" % testpath2)

        assert stat != 0, "subdir auto unmount failed!"

    def test_multi_subdir(self):
        """
        3127 同时删除多个子目录，客户端执行df命令，可以触发多个挂载点自动卸载
        """
        try:
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            for i in range(1, 10):
                testdir = self.testdir + str(i)
                self.sshserver.ssh_exec("cd %s&&mkdir %s" % (self.MOUNT_DIR, testdir))
                self.sshserver.ssh_exec(self.get_cli("acl_ip_add", testdir, "*", "rw"))
                # 添加挂载点
                mount_conf = "%s /etc/yrfs/yrfs-client.conf /%s" % (self.MOUNT_DIR + str(i), testdir)
                self.sshclient.ssh_exec("echo \"%s\" >> %s" % (mount_conf, consts.CLIENT_MOUNT_FILE))
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            # 删除子目录
            self.sshserver.ssh_exec("cd %s&&rm -fr %s*" % (self.MOUNT_DIR, self.testdir))
            sleep(2)
            # 指定第一次df
            self.sshclient.ssh_exec("df -h")
            stat, _ = self.sshclient.ssh_exec("df -h|grep %s" % self.MOUNT_DIR)
            assert stat != 0, "Expect df failed."
            sleep(1)
            # 执行第二次df
            self.sshclient.ssh_exec("df -h")
            stat, _ = self.sshclient.ssh_exec("cat /etc/mtab|grep %s" % self.MOUNT_DIR)
            assert stat != 0, "Expect mtab failed."
        finally:
            for i in range(1, 10):
                testdir = self.testdir + str(i)
                self.sshserver.ssh_exec(self.get_cli("acl_ip_del", testdir, "*"))
            self.sshserver.ssh_exec("cd %s&&rm -fr %s*" % (self.MOUNT_DIR, self.testdir))
