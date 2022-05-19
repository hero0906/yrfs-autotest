# coding=utf-8
'''
@Desciption : acl cidr case
@Time : 2021/03/24 14:53
@Author : caoyi
'''

import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.client import client_mount

@pytest.mark.smokeTest
class TestaclCidr(YrfsCli):

    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]

    def test_cidr(self):
        '''
        bugID: 3869 【6.5.3】acl的cidr权限错误,子网掩码错误换算错误问题。
        '''
        sshserver = sshClient(self.serverip)
        try:
            #获取当前的子网网段，然后将修改后的子网掩码加入acl cidr，使用原来的客户端预期是挂载失败的。
            _, netfile = sshserver.ssh_exec("cat %s|head -n 1" % consts.CLIENT_NET_FILE)
            #取集群网段的第三位，并且加1，以此作为acl的cidr的ip地址。
            cidr_list = []

            ip_cidr = netfile.split('/')
            ip_seg = ip_cidr[0].split('.')
            for n, m in enumerate(ip_seg):
                if m == "0":
                    break
            num = 0
            for i in ip_seg:
                if num == n - 1:
                    i = str(int(i) + 1)
                num = num + 1
                cidr_list.append(i)

            new_cidr_ip = ".".join(cidr_list) + "/" + ip_cidr[1]
            #设置cidr acl
            set_stat, _ = sshserver.ssh_exec(self.get_cli("acl_ip_add","",new_cidr_ip,"rw"))
            #客户端挂载
            mount_stat = client_mount(self.clientip)
            #检查点校验
            assert mount_stat != 0, "expected result:client mount failed."
            assert set_stat == 0, "expected result:acl cidr set success."
        finally:
            sshserver.ssh_exec(self.get_cli("acl_ip_del","",new_cidr_ip))
            sshserver.close_connect()
        # sshserver = sshClient(self.serverip)
        # cidr_ip = ""
        # try:
        #     #获取当前的子网网段，然后将修改后的子网掩码加入acl cidr，使用原来的客户端预期是挂载失败的。
        #     _, netfile = sshserver.ssh_exec("cat %s|head -n 1" % consts.CLIENT_NET_FILE)
        #     #取集群网段的第三位，并且加1，以此作为acl的cidr的ip地址。
        #     cidr_list = []
        #     num = 0
        #     for n in netfile.split('.'):
        #         if num == 1:
        #             n = str(int(n) + 1)
        #         cidr_list.append(n)
        #         num = num +1
        #     cidr_ip = ".".join(cidr_list)
        #     #设置cidr acl
        #     set_stat, _ = sshserver.ssh_exec(self.get_cli("acl_ip_add","",cidr_ip,"rw"))
        #     #客户端挂载
        #     mount_stat = client_mount(self.clientip)
        #     #检查点校验
        #     assert mount_stat != 0, "expected result:client mount failed."
        #     assert set_stat == 0, "expected result:acl cidr set success."
        # finally:
        #     sshserver.ssh_exec(self.get_cli("acl_ip_del","",cidr_ip))
        #     sshserver.close_connect()