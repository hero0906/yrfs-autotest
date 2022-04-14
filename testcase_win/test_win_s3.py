#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : test win s3
@Time : 2021/12/20 19:57
@Author : caoyi
"""
import time
from config import consts
from common.util import sshClient
from depend.client import win_client_mount
from common.cli import YrfsCli

class TestS3(YrfsCli):
    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.WINCLIENT
        self.sshserver = sshClient(self.serverip)
        self.sshclient = sshClient(self.clientip, linux=False)

    def test_win_add_s3(self):
        """
        3286 校验添加对象存储支持win客户端
        """
        testdir = "autotest_win_" + time.strftime("%m-%d-%H%M%S")
        mountdir = consts.MOUNT_DIR
        tiering_id = "999"
        #添加bucket
        bucket_add = self.get_cli("bucket_add", consts.s3["hostname"], consts.s3["protocol"],
                                  consts.s3["bucketname"],
                                  consts.s3["uri_style"], consts.s3["region"], consts.s3["access_key"],
                                  consts.s3["secret_access_key"],
                                  consts.s3["token"], consts.s3["type"], consts.s3["bucketid"])
        try:
            self.sshserver.ssh_exec(self.get_cli("bucket_del", consts.s3["bucketid"]))
            self.sshserver.ssh_exec(bucket_add)
            #创建测试目录
            self.sshserver.ssh_exec("cd %s&&mkdir -p %s" % (mountdir, testdir))
            #创建测试数据
            self.sshserver.ssh_exec("cd %s&&dd if=/dev/zero of=%s/file1 bs=1M count=1000" % (mountdir, testdir))
            #客户端挂载
            win_client_mount(self.clientip, subdir=testdir, acl_add=True)
            #对接对象存储
            add_tier = self.get_cli("tiering_add", testdir, consts.s3["bucketid"], "1", "00:00,05:00", tiering_id)
            stat, _ = self.sshserver.ssh_exec(add_tier)
            assert stat == 0, "add tiering failed."
            #数据写入
            stat, _ = self.sshclient.ssh_exec("copy z:\\file1 z:\\file2")
            assert stat == 0, "Create file failed."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))


