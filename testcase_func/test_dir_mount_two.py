#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Description : dir mount two client test suite
@Time : 2021/11/11 14:55
@Author : caoyi
"""
import pytest
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount


class Test_twoClient(YrfsCli):
    def setup_class(self):
        if len(consts.CLIENT) < 2:
            pytest.skip(msg="need two client", allow_module_level=True)
        self.serverip = consts.META1
        self.client1 = consts.CLIENT[0]
        self.client2 = consts.CLIENT[1]

        self.sshserver = sshClient(self.serverip)
        self.sshclient1 = sshClient(self.client1)
        self.sshclient2 = sshClient(self.client2)
        self.mountdir = consts.MOUNT_DIR

        self.add_acl = self.get_cli(self, "acl_ip_add")
        self.del_acl = self.get_cli(self, "acl_ip_del")

    def teardown_class(self):
        self.sshserver.close_connect()
        self.sshclient2.close_connect()
        self.sshclient1.close_connect()

    @pytest.mark.parametrize("mode1, mode2", (("rw", "rw"), ("rw", "ro"), ("ro", "ro")))
    #@pytest.mark.parametrize("mode1, mode2", (("ro", "ro"),))
    def test_diff_dir_diff_client(self, mode1, mode2):
        """
        2027 不同挂载点挂载到不同客户端的相同目录，设置读写权限
        2028 不同挂载点挂载到不同客户端的相同目录，设置只读权限
        """
        dir1 = "autotest_acl_2027"
        dir2 = "autotest_acl_2028"
        try:
            self.sshserver.ssh_exec("cd %s&&mkdir -p %s %s" % (self.mountdir, dir1, dir2))
            # 设置acl权限
            self.sshserver.ssh_exec(self.add_acl.format(dir1, "*", mode1))
            self.sshserver.ssh_exec(self.add_acl.format(dir2, "*", mode2))
            # 客户端挂载
            m1 = client_mount(self.client1, dir1)
            m2 = client_mount(self.client2, dir2)
            assert m1 == 0 and m2 == 0, "client mount failed."
            t1, _ = self.sshclient1.ssh_exec("cd %s&&touch file1" % (self.mountdir))
            t2, _ = self.sshclient2.ssh_exec("cd %s&&touch file1" % (self.mountdir))
            # 校验权限是否正确
            if mode1 == "rw":
                assert t1 == 0, "touch failed."
            else:
                assert t1 != 0, "touch success."
            if mode2 == "rw":
                assert t2 == 0, "touch failed."
            else:
                assert t2 != 0, "touch success"

        finally:
            self.sshserver.ssh_exec(self.del_acl.format(dir1, "*"))
            self.sshserver.ssh_exec(self.del_acl.format(dir2, "*"))
            self.sshserver.ssh_exec("cd %s&&rm -fr %s %s" % (self.mountdir, dir1, dir2))
