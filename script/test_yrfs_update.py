# coding=utf-8
"""
@Desciption : yrfs yum update
@Time : 2020/5/27 18:47
@Author : caoyi
"""
import pytest
from config import consts
from common.cli import YrfsCli
from common.util import sshClient
from common.cluster import get_Cluster_Hostip, check_cluster_health
import logging
import re
import datetime
from time import sleep

logger = logging.getLogger(__name__)

#@pytest.mark.skip(msg="skip not finish.")
@pytest.mark.serviceTest
class TestyumUpdate(YrfsCli):
    '''
    集群yum update更新，可选操作。
    '''
    def setup_class(self):
        #连接server
        self.serverip = consts.META1
        self.sshserver1 = sshClient(self.serverip)
        #查看当前yrfs版本
        version_stat, version_res = self.sshserver1.ssh_exec(self.get_cli(self, "yrfs_version"))
        yrfs_version_tmp = re.findall("Version:(.*)",version_res)
        yrfs_version = ''.join(yrfs_version_tmp)[:3]
        logger.info("yrfs version: %s" % yrfs_version)
        #查询mds的数量
        _, mds_num = self.sshserver1.ssh_exec("df -h|grep mds|wc -l")
        logger.info("cluster mds num: %s" % mds_num)
        #根据版本判断服务名称
        self.client = "yrfs-client"
        self.mgr = "yrfs-mgmtd"
        self.oss = "yrfs-storage"
        self.agent = "yrfs-admon"
        self.mds = "yrfs-meta"
        if mds_num == "2":
            self.mds = "yrfs-meta@mds0 yrfs-meta@mds1"
        if yrfs_version == "6.3":
            self.repo_path = "http://10.16.0.22:17285"
        elif yrfs_version == "6.5":
            self.repo_path = "http://10.16.0.22:17283"
        elif yrfs_version == "6.6":
            self.repo_path = "http://10.16.0.22:17284"
            self.mgr = "yrfs-mgr"
            self.oss = "yrfs-oss"
            self.agent = "yrfs-agent"
            self.mds = "yrfs-mds@mds0"
            if mds_num == "2":
                self.mds = "yrfs-mds@mds0 yrfs-mds@mds1"
        #yum repo配置命令
        self.repo_bakdir = "autotest_bak_" + datetime.datetime.now().strftime('%H%M%S')
        self.repo = "mkdir -p /etc/yum.repos.d/{0};mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/{0};".format(self.repo_bakdir)  + \
                    "echo -e \"[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=%s\ngpgcheck=0\" > "\
                    "/etc/yum.repos.d/autotest-yrcf.repo" % self.repo_path
        #UI服务升级命令
        self.dashboard = "systemctl restart yrcloudfile-dashboard && service inert-krypton-host restart"
        self.pcs = "pcs resource restart krypton-api-clone&&pcs resource restart krypton-cluster&&" \
                    "su -s /bin/sh -c \"krypton-dbsync\" krypton"
        #yum update命令
        self.yum_update_cmd = ["yum clean","yum makecache","rpm -qa|grep -E \"yrfs|yanrong\"|xargs yum -y update","systemctl daemon-reload"]
        #客户端包获取
        self.ubuntu_rpm = ["wget -c -r -nd -np -k -L -A deb http://192.168.0.22:17282/v66x-daily/daily-build/clients/ubuntu2004/ -P /autotest_rpm",
                      "dpkg -i /autotest_rpm/yrfs-client*.deb","rm -fr /autotest_rpm"]
        self.centos_rpm = ["wget -c -r -nd -np -k -L -A rpm http://192.168.0.22:17282/v66x-daily/daily-build/rpms/ -P /autotest_rpm",
                      "rpm -Uvh /autotest_rpm/yrfs-*.rpm","systemctl daemon-reload","rm -fr /autotest_rpm"]
        #获取集群节点的ipv4管理网ip地址
        server_mgmt_ips_tmp = get_Cluster_Hostip()
        self.server_mgmt_ips = [i[1] for i in server_mgmt_ips_tmp.values()]
        logger.info("get cluster mgmt ips: %s." % self.server_mgmt_ips)

    def teardown_class(self):
        self.sshserver1.close_connect()

    def test_hot_update(self):
        '''
        测试yrfs热升级,目前公司内部采用的热升级操作，其他环境不支持。
        '''
        #server节点服务更新
        num = 1
        for serverip in self.server_mgmt_ips:
            logger.info("update node: %s." % serverip)
            self.sshserver = sshClient(serverip)
            try:
                #配置yum仓库
                self.sshserver.ssh_exec(self.repo)
                #执行升级yum安装服务重启
                for yum_cmd in self.yum_update_cmd:
                    self.sshserver.ssh_exec(yum_cmd)
                #清理yum 仓库
                self.sshserver.ssh_exec("mv /etc/yum.repos.d/{0}/* /etc/yum.repos.d/;rm -fr /etc/yum.repos.d/autotest*".format(self.repo_bakdir))
                for service in self.agent, self.mgr, self.mds, self.oss, self.client:
                    #服务stop yrfs
                    stop_cmd = "systemctl restart " + service
                    self.sshserver.ssh_exec(stop_cmd)
                    sleep(1)
                # stop UI服务
                if num == 1:
                    self.sshserver.ssh_exec(self.pcs)
                if num <= 4:
                    self.sshserver.ssh_exec(self.dashboard)
                num += 1
            finally:
                self.sshserver.close_connect()
        #检查集群恢复正常
        check_cluster_health()

    def test_client_update(self):
        #升级客户端版本
        try:
            client1 = consts.CLIENT[0]
            self.sshclient1 = sshClient(client1)
            if len(consts.CLIENT) > 2:
                client2 = consts.CLIENT[1]
                self.sshclient2 = sshClient(client2)
                #客户端2为ubuntu
                for rpm in self.ubuntu_rpm:
                    self.sshclient2.ssh_exec(rpm)
            #客户端升级包安装，这里使用的是超威一个是centos一个是ubuntu安装包
            for rpm in self.centos_rpm:
                self.sshclient1.ssh_exec(rpm)
        finally:
            self.sshclient1.close_connect()
            if len(consts.CLIENT) > 2:
                self.sshclient2.close_connect()