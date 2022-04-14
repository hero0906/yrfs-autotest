# coding=utf-8
'''
@Desciption : quota depth move testcase.
@Time : 2021/03/23 14:44
@Author : caoyi
'''

import pytest
import os
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from time import sleep

@pytest.mark.funcTest
class TestquotaMove(YrfsCli):
    serverip = consts.META1

    def test_subdir_mv(self):
        '''
        bugID: 3983【quota】对父目录设置qos和quota，在该目录下做深度目录间的跨目录操作，quota会自动生成深度目录配置信息.
        '''
        try:
            sshserver = sshClient(self.serverip)
            testdir1 = "autotest/1/2/3/4"
            testdir2 = "autotest/5"
            testdir3 = "autotest/1/2"

            testpath1 = consts.MOUNT_DIR + "/" + testdir1
            testpath2 = consts.MOUNT_DIR + "/" + testdir2
            testpath3 = consts.MOUNT_DIR + "/" + testdir3
            #创建测试目录
            sshserver.ssh_exec("mkdir -p %s" % testpath1)
            sshserver.ssh_exec("mkdir -p %s" % testpath2)
            #设置quota信息
            quota_set_cmd = self.get_cli("quota_set",testdir1,"20G","1000")
            quota_stat, _ = sshserver.ssh_exec(quota_set_cmd)
            #mv 目录操作
            sleep(5)
            mv_stat, _ = sshserver.ssh_exec("mv %s %s" % (testpath3, testpath2))
            #查询mv后quota信息
            _, quota_list = sshserver.ssh_exec(self.get_cli("quota_list"))
            #校验点验证
            assert quota_stat == 0, "expected result, set quota success."
            assert mv_stat == 0, "expected result, mv dir success."
            assert "/autotest/5/2/3/4" in quota_list, "expected result, dir in quota list."
            sleep(5)

        finally:
            sshserver.ssh_exec("rm -fr " + os.path.join(consts.MOUNT_DIR, "autotest"))
            sshserver.close_connect()
            sleep(2)

    @pytest.mark.skip(reason="expect skip, Not need test")
    def test_sixteen_mv(self):
        """
        bugID:  3983【qos】对父目录设置qos和quota，mv后qos目录长度超过16级限制后是否会成功
        """
        try:
            sshserver = sshClient(self.serverip)
            testdir1 = "autotest/1/2/3/4"
            testdir2 = "autotest/2/3/4/5/6/7/8/9/10/11/12/13/14/15"
            testdir3 = "autotest/1"

            testpath1 = consts.MOUNT_DIR + "/" + testdir1
            testpath2 = consts.MOUNT_DIR + "/" + testdir2
            testpath3 = consts.MOUNT_DIR + "/" + testdir3
            #创建测试目录：
            sshserver.ssh_exec("mkdir -p %s" % testpath1)
            sshserver.ssh_exec("mkdir -p %s" % testpath2)
            #设置quota信息
            quota_set_cmd = self.get_cli("quota_set",testdir1,"20G","1000")
            quota_set_stat, _ = sshserver.ssh_exec(quota_set_cmd)
            sleep(5)
            #mv操作
            mv_stat, _ = sshserver.ssh_exec("mv %s %s" % (testpath3, testpath2))
            sleep(5)
            assert quota_set_stat == 0, "expected result, quota set success."
            assert mv_stat != 0, "expected result, quota dir mv failed."

        finally:
            sshserver.ssh_exec("rm -fr %s" % os.path.join(consts.MOUNT_DIR, "autotest"))
            sshserver.close_connect()
            sleep(2)