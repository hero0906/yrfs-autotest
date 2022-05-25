#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : client native cache
@Time : 2021/10/22 15:22
@Author : caoyi
"""

import pytest
import logging
from depend.client import client_mount
from config import consts
from common.cli import YrfsCli
from common.util import sshClient, sshSftp

logger = logging.getLogger(__name__)

@pytest.mark.funcTest
class Test_pageCache(YrfsCli):
    """
    客户端缓存page cache测试用例集
    """
    def setup_class(self):
        #判断版本选择cache配置
        self.cache_param = "client_cache_type = cache"

        self.clientip = consts.CLIENT[0]
        serverip = consts.META1

        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(serverip)
        #添加acl权限
        self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_add", "", "*", "rw"))
        _mount = client_mount(self.clientip, param=self.cache_param)
        assert _mount == 0, "client mount failed"

    def teardown_class(self):
        self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_del", "", "*"))
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_dd(self):
        """
        2266 dd相关测试
        """
        testfile = consts.MOUNT_DIR + "/autotest_dd_file1"

        try:

            for bs in (4,16,64,128,1024):
                for count in (4,16,64,128,1024):
                    ddstat, _ = self.sshclient.ssh_exec("dd if=/dev/zero of=%s bs=%sk count=%s"
                                                        % (testfile, bs, count))
                    assert ddstat == 0,"dd failed"
                    ddstat, _ = self.sshclient.ssh_exec("dd if=%s of=/dev/zero bs=%sk count=%s"
                                                        % (testfile, bs, count))
                    assert ddstat == 0, "dd failed"

            ddstat, _ = self.sshclient.ssh_exec("dd if=/dev/zero of=%s bs=513k count=1" % testfile)
            assert ddstat == 0, "dd failed"
            ddstat, _ = self.sshclient.ssh_exec("dd if=/dev/zero of=%s  bs=513k count=1 oflag=append conv=notrunc"
                                                % testfile)
            assert ddstat == 0, "dd failed"
            ddstat, _ = self.sshclient.ssh_exec("dd if=/dev/zero of=%s bs=1k count=128 oflag=direct" % testfile)
            assert ddstat == 0, "dd failed"

        finally:

            self.sshserver.ssh_exec("rm -fr %s" % testfile)

    def test_copy_bigfile(self):
        """
        2265 拷贝一个大文件，卸载客户端，再重挂载，比较前后的MD5值
        """
        testfile = consts.MOUNT_DIR + "/autotest_copy_bigfile1"

        try:
            ddstat, _ = self.sshclient.ssh_exec("dd if=/dev/zero of=%s bs=1M count=5024" % testfile)
            assert ddstat == 0,"dd failed"
            stat, md1 = self.sshclient.ssh_exec("md5sum " + testfile)
            assert stat == 0, "md5sum failed"
            #卸载
            self.sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            #重新挂载客户端
            client_mount(self.clientip, param=self.cache_param)
            #再次计算md5值
            stat, md2 = self.sshclient.ssh_exec("md5sum " + testfile)
            assert stat == 0, "md5sum failed"
            #校验md5值一致
            assert md1 == md2, "md5sum inconformity"
        finally:
            self.sshserver.ssh_exec("rm -fr " + testfile)

    def test_posix(self):
        """
        2243 （自动化）验证posix语义正确性
        """
        fstest_dir = "/opt/pjdfstest-yrfs"
        #检验prove工具是否安装
        stat, _ = self.sshclient.ssh_exec("which prove")
        if stat != 0:
            self.sshclient.ssh_exec("yum -y install perl-Test-Harness")
        stat, _ = self.sshclient.ssh_exec("which prove")
        if stat != 0:
            logger.error("Not Found prove test skip")
            pytest.skip(msg="not found prove tools.")
        #验证客户端的fstest安装包是否存在.不存在的话就拷贝
        stat, _ = self.sshclient.ssh_exec("stat " + fstest_dir)
        if stat != 0:
            sshsftp = sshSftp(self.clientip)
            sshsftp.sftp_upload("tools/pjdfstest-yrfs.tar.gz", "/opt/pjdfstest-yrfs.tar.gz")
            sshsftp.close_connect()
            self.sshclient.ssh_exec("tar -zxvf /opt/pjdfstest-yrfs.tar.gz -C /opt")

        logger.info("Run fstest %s" % consts.MOUNT_DIR)

        fstest_stat, _ = self.sshclient.ssh_exec("cd %s&&prove -rQ %s" % (consts.MOUNT_DIR, fstest_dir))

        assert fstest_stat == 0, "fstest failed."