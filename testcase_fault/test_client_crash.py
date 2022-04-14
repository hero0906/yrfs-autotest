# coding=utf-8
'''
@Desciption : client crash case suite.
@Time : 2021/03/23 14:44
@Author : caoyi
'''

import pytest
from time import sleep
from common.cli import YrfsCli
from config import consts
from depend.client import client_mount
from common.util import sshClient

@pytest.mark.faultTest
class TestclientCrash(YrfsCli):

    def test_client_mount(self):
        '''
        bugID: 3953 【6.5.4】输入非法的mgmt_hosts参数，客户端会crash
        '''
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        try:
            sshserver = sshClient(self.serverip)
            sshclient = sshClient(self.clientip)
            aclid = "autotest"
            #客户端挂载
            sshserver.ssh_exec(self.get_cli("acl_id_add","",aclid,"rw"))
            mount_stat = client_mount(self.clientip,aclid=aclid)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed,test quit.")
            #修改客户端挂载参数并重新启动
            stop_stat, _ = sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
            assert stop_stat == 0, "expected result,stop client success."

            sed_cmd = "sed -i \"s/^cluster_addr.*/cluster_addr = mgmt_ip6/g\" %s" % consts.CLIENT_CONFIG
            sshclient.ssh_exec(sed_cmd)

            mount_stat, _ = sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            # assert mount_stat != 0, "expected result,mount fail."
            #执行一条命令验证客户端系统是否正常
            sleep(5)
            check_stat, _ = sshclient.ssh_exec("uname -a")
            assert check_stat == 0, "expected result, check status system ok."

        finally:

            sshserver.ssh_exec(self.get_cli("acl_id_del","",aclid))
            sshclient.close_connect()
            sshserver.close_connect()