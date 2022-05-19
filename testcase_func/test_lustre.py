#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : lustre test suite
@Time : 2021/12/29 14:55
@Author : caoyi
"""
#import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.client import client_mount, run_lustre
from common.cluster import check_cluster_health


class TestlustrePosix(YrfsCli):

    #@pytest.mark.timeout(600)
    def test_lustre(self):
        """
        lustre posix test
        """
        serverip = consts.META1
        clientip = consts.CLIENT[0]
        sshserver = sshClient(serverip)
        try:
            # 设置acl
            sshserver.ssh_exec(self.get_cli("acl_ip_add", "", "*", "rw"))
            # 客户端挂载
            stat = client_mount(clientip)
            assert stat == 0, "client mount failed"
            # 执行lustre测试
            run_lustre(clientip)
            # 检查集群正常
            check_cluster_health(check_times=1)
        finally:
            sshserver.ssh_exec(self.get_cli("acl_ip_del", "", "*"))
