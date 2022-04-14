# coding=utf-8
'''
@Desciption : qos ls 2000 dir.
@Time : 2021/03/23 10:06
@Author : caoyi
'''

import pytest
from common.cluster import check_cluster_health
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from time import sleep

#@pytest.mark.skip(msg="time too long")
@pytest.mark.faultTest
class Testqosls(YrfsCli):

    serverip = consts.META1

    def test_ls_qosdir(self):
        '''
        bugID:  3530 【6.5.0】【qos】ls 两千个qos目录导致系统宕掉，连续出现多次。
        '''
        qos_cmd = self.get_cli("qos_total_set")
        try:
            sshserver = sshClient(self.serverip)
            for num in range(1,2000):
                #创建测试目录
                rootdir = consts.MOUNT_DIR + "/autotest"
                testdir = "autotest/dir" + str(num)
                testpath = consts.MOUNT_DIR + "/" + testdir
                sshserver.ssh_exec("mkdir -p " + testpath)
                #设置qos
                qos_set_cmd = qos_cmd.format(testdir, "10G", "1000", "20000")
                qos_set_stat, _ = sshserver.ssh_exec(qos_set_cmd)
                assert qos_set_stat == 0, "set qos failed."
            #ls qos目录
            ls_stat, _ = sshserver.ssh_exec("ls " + rootdir)
            assert ls_stat == 0, "ls 2000 qos dir success."
        finally:
            sleep(5)
            sshserver.ssh_exec("rm -fr " + rootdir)
            sshserver.close_connect()
            sleep(5)
            check_cluster_health()
