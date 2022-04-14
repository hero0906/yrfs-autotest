#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : qos dir perfamance test
@Time : 2021/11/19 11:50
@Author : caoyi
"""
import logging
import os
import time

import pytest

from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount
from depend.perftest import fio_test

logger = logging.getLogger(__name__)


class Test_qosPerf(YrfsCli):

    def setup_class(self):
        self.server = consts.META1
        self.client = consts.CLIENT[0]
        self.testdir = "autotest_qos_perf_" + time.strftime("%m-%d-%H%M%S")
        self.mountdir = consts.MOUNT_DIR
        self.testpath = os.path.join(self.mountdir, self.testdir)
        self.sshserver = sshClient(self.server)
        self.sshclient = sshClient(self.client)
        # 创建初始测试目录
        self.sshserver.ssh_exec("cd %s&&mkdir %s" % (self.mountdir, self.testdir))
        # 客户端挂载
        stat = client_mount(self.client, acl_add=True)
        assert stat == 0, "Client mount failed."
        # 初始性能
        self.init_perf = fio_test(self.client, self.testpath, times=10)

    def teardown_class(self):
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    @pytest.mark.parametrize("settype", ("total", "part"))
    def test_qos_perf(self, settype):
        """
        设置qos前后对比性能测试
        """
        try:
            # total设置qos
            if settype == "total":
                self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, "100G", "10000000", "0"))
            else:
                self.sshserver.ssh_exec(
                    self.get_cli("qos_part_set", self.testdir, "100G", "100G", "10000000", "10000000", "0"))
            # 第二次测试性能
            time.sleep(5)
            end_perf = fio_test(self.client, self.testpath)
            # 对比性能测试,前后无偏差
            for m, n in zip(self.init_perf.values(), end_perf.values()):
                logger.info("Init perf: %s, end perf: %s" % (m, n))
                assert int(m) * 0.8 < int(n) < int(
                    m) * 1.2, "The performance is different before and after qos Settings"
        finally:
            self.sshserver.ssh_exec(self.get_cli("qos_remove", self.testdir))
            self.sshclient.ssh_exec("killall -9 fio")