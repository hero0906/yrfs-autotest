# coding=utf-8
'''
@Desciption : yrcli command file create test
@Time : 2021/03/19 9:27
@Author : caoyi
'''

import os
import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient

@pytest.mark.smokeTest
class TestcreateFile(YrfsCli):
    '''
    测试命令文件创建集合
    '''

    def setup_class(self):
        self.serverip = consts.META1
        self.sshclient = sshClient(self.serverip)
        self.testfile = "autotest_creatfile"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testfile)

    def teardown_class(self):
        self.sshclient.ssh_exec("rm -fr " + self.testpath)
        self.sshclient.close_connect()

    def test_create_file(self):
        '''
        bugID:  4141 【6.5.6】【文件创建】执行yrcli --create报错，无法识别mirror参数。
        '''
        self.sshclient.ssh_exec("rm -fr " + self.testpath)

        #文件创建
        create_cmd = self.get_cli("create_file","1m","4",self.testfile,"mirror")
        create_stat, _ = self.sshclient.ssh_exec(create_cmd)
        #验证文件是否创建成功
        file_stat, _ = self.sshclient.ssh_exec("stat " + self.testpath)
        _, entry_res = self.sshclient.ssh_exec(self.get_cli("get_entry",self.testfile))

        #校验点
        assert file_stat == 0, "check file stat failed."
        assert "Meta Redundancy: Mirror" in entry_res, "check file mirror failed."