# coding=utf-8

'''
@Desciption : client cliacl testcase
@Time : 2020/10/20 18:58
@Author : caoyi
'''

import pytest
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec, sshClient
from common.cluster import get_client_storageip


@pytest.mark.smokeTest
class Test_client_cliacl(YrfsCli):

    def setup_class(self):
        self.server = consts.META1
        self.client = consts.CLIENT[0]

        self.client_storage_ip = get_client_storageip(self.client)

        self.sshclient = sshClient(self.client)
        self.sshserver = sshClient(self.server)

        self.utils_rpm_stat, _ = self.sshclient.ssh_exec("rpm -qa|grep yrfs-utils")

        if self.utils_rpm_stat == 0:
            #验证ip4的cliacl权限需要配置client端mgmt参数：
            get_mgmt_cmd = self.get_cli(self, 'oss_node') + "|grep IPv4 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|" + \
                  "awk -F '<' '{print $2}'|uniq|head -n 3"

            _, mgmt_ip4_tmp = self.sshserver.ssh_exec(get_mgmt_cmd)
            mgmt_ip4 = ",".join(mgmt_ip4_tmp.split('\n'))

            # 写入配置文件yrfs-client.conf
            self.sshclient.ssh_exec('echo "cluster_addr = %s" > %s' % (mgmt_ip4, consts.CLIENT_CONFIG))
            # 配置net文件
            _, net_config = self.sshserver.ssh_exec("cat " + consts.CLIENT_NET_FILE)
            self.sshclient.ssh_exec("echo \"%s\" > %s" % (net_config, consts.CLIENT_NET_FILE))
        self.sshserver.ssh_exec(self.get_cli(self, 'cliacl_del', "*"))

    def teardown_class(self):
        self.sshclient.close_connect()
        self.sshserver.close_connect()

    def test_cliacl_ip_add(self):
        '''
        测试命令行添加cliacl权限
        '''
        cmd = self.get_cli('cliacl_add', self.client_storage_ip)
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "add cliacl failed."

   #@pytest.mark.skipif(self.utils_rpm_stat != 0,reason="no install yrfs-utils rpm")
    def test_cliacl_privi_avail(self):
        '''
        验证客户端权限可用
        '''
        if self.utils_rpm_stat != 0:
            pytest.skip(msg="not install utils tools")

        cmd = self.get_cli('cliacl_list')
        res = ssh_exec(self.client, cmd)
        assert self.client_storage_ip in res

    def test_cliacl_list(self):
        '''
        列出cliacl ip地址
        '''
        cmd = self.get_cli('cliacl_list')
        res = ssh_exec(self.server, cmd)
        assert self.client_storage_ip in res

    def test_cliacl_ip_del(self):
        '''
        测试删除cliacl ip
        '''
        cmd = self.get_cli('cliacl_del', self.client_storage_ip)
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "delete cliacl ip failed."

    #@pytest.mark.skipif(utils_rpm_stat != 0, reason="no install yrfs-utils rpm")
    def test_cliacl_privi_unavail(self):
        '''
        测试无权限cliacl不可用
        '''
        if self.utils_rpm_stat != 0:
            pytest.skip(msg="not install utils tools")
        cmd = self.get_cli('cliacl_list')
        res = ssh_exec(self.client, cmd)
        assert 'Permission denied' in res