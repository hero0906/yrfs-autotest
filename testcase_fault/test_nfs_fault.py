#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : nfs fault case
@Time : 2021/12/10 17:07
@Author : caoyi
"""
import time, os, pytest
from config import consts
from common.util import sshClient
from depend.nfsdepend import NfsRest
#from common.fault import makeFault
from depend.client import run_vdbench
from common.cluster import check_cluster_health, ping_test, get_netcard_info

@pytest.mark.skip
class TestNfsFault():
    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.sshserver = sshClient(self.serverip)
        self.sshclient = sshClient(self.clientip)
        #创建测试目录
        self.testdir = "autotest_nfs_" + time.strftime("%m-%d-%H%M%S")
        self.mountdir = consts.MOUNT_DIR
        self.testpath = os.path.join(self.mountdir, self.testdir)
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)
        #获取dns域名
        self.nfsrest = NfsRest()
        self.nfs_domain = self.nfsrest.get_dns_name()
        if not self.nfs_domain:
            pytest.skip(msg="not found nfs domain", allow_module_level=True)
        #配置dns 解析
        self.dns_ips = self.nfsrest.get_dns_ip()
        for ip in self.dns_ips:
            stat, _  = self.sshclient.ssh_exec("cat /etc/resolv.conf|grep " + ip)
            if stat != 0:
                self.sshclient.ssh_exec("sed -i '1 i nameserver %s' /etc/resolv.conf" % ip)
        # 创建nfs share
        time.sleep(5)
        self.target_id, self.share_id = self.nfsrest.add_share(self.testdir)
        #挂载命令
        self.mount_nfs = "mount -t nfs {0}:{1}/{2} {1}".format(self.nfs_domain, self.mountdir, self.testdir)
        time.sleep(10)
        self.sshclient.ssh_exec("umount {0};mkdir {0}".format(self.mountdir))

    def teardown_class(self):
        #清除共享和目录
        self.sshserver = sshClient(self.serverip)
        self.nfsrest.del_share(self.target_id, self.share_id)
        self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
        self.sshclient.close_connect()
        self.sshserver.close_connect()
    #
    # def setup(self):
    #     self.sshserver = sshClient(self.serverip)
    # def teardown(self):
    #     self.sshserver.close_connect()
    @pytest.mark.parametrize("nodetype", ("master", "slave"))
    def test_reboot_dns_master(self, nodetype):
        """
        3529 reboot主DNS服务或者是DNS服务从节点所在节点，包含两条case
        """
        try:
            # 挂载nfs
            self.sshclient.ssh_exec(self.mount_nfs)
            #vdbench 业务运行
            stat = run_vdbench(self.testpath)
            assert stat == 0, "vdbench run failed."
            #故障dns master或者slave
            if nodetype == "master":
                dns_master_ip = self.dns_ips[0]
            else:
                dns_master_ip = self.dns_ips[1]
            sshmaster = sshClient(dns_master_ip)
            sshmaster.ssh_exec("reboot -f > /dev/null 2>&1 &", timeout=5)
            sshmaster.close_connect()
            time.sleep(10)
            #ping验证
            for i in range(60):
                stat = ping_test(dns_master_ip)
                if not stat:
                    time.sleep(10)
                else:
                    break
            else:
                raise AssertionError("HOST unreachable.")
            time.sleep(10)
            check_cluster_health()
            #检查客户端业务正常
            stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench")
            assert stat == 0, "vdbench exit"
            #清理掉vdbench业务
            self.sshclient.ssh_exec("ps axu|grep vdbench|awk '{print $2}'|xargs -I {} kill -9 {}")
            #验证客户端重新挂载是否正常
            stat, _ = self.sshclient.ssh_exec("umount " + self.mountdir)
            assert stat == 0, "umount nfs client failed."
            stat, _ = self.sshclient.ssh_exec(self.mount_nfs)
            assert stat == 0, "Nfs client mount failed."
        finally:
            # self.sshclient.ssh_exec("killall -9 vdbench")
            self.sshclient.ssh_exec("ps axu|grep vdbench|awk '{print $2}'|xargs -I {} kill -9 {}")
            self.sshclient.ssh_exec("umount " + self.mountdir)
            check_cluster_health()

    @pytest.mark.parametrize("nettype", ("mgmt","storage","all"))
    def test_down_mgmt_net(self, nettype):
        """
        3530 down掉主DNS服务所在节点管理网卡、存储网卡、或者是全部网卡包含三条case
        """
        global dns_master_ip
        try:
            # 挂载nfs
            stat, _ = self.sshclient.ssh_exec(self.mount_nfs)
            assert stat == 0,"mount nfs failed."
            #vdbench 业务运行
            stat = run_vdbench(self.testpath)
            assert stat == 0, "vdbench run failed."
            #故障dns master管理网网卡
            dns_master_ip = self.dns_ips[0]
            sshmaster = sshClient(dns_master_ip)
            #获取管理网或者存储网网卡名称
            netcard_info = list(get_netcard_info().values())[0]
            mgmt_net = netcard_info[1][0]
            storage_net = netcard_info[0][0]
            #故障dns主的管理网网卡、存储网卡、或者全部网卡
            if nettype == "mgmt":
                sshmaster.ssh_exec("nohup sleep 5;ifdown {0};sleep 40;ifup {0} 2>&1 &".format(mgmt_net))
            if nettype == "storage":
                sshmaster.ssh_exec("nohup sleep 5;ifdown {0};sleep 40;ifup {0} 2>&1 &".format(storage_net))
            else:
                sshmaster.ssh_exec("nohup sleep 5;ifdown {0};ifdown {1};sleep 40;ifup {0};ifup {1} 2>&1 &".format(mgmt_net,
                                                                                                    storage_net))
            sshmaster.close_connect()
            #检查客户端业务正常
            time.sleep(30)
            stat, _ = self.sshclient.ssh_exec("ps axu|grep vdbench")
            assert stat == 0, "vdbench exit"
            #清理掉vdbench业务
            self.sshclient.ssh_exec("ps axu|grep vdbench|awk '{print $2}'|xargs -I {} kill -9 {}")
            #验证客户端重新挂载是否正常
            stat, _ = self.sshclient.ssh_exec("umount " + self.mountdir)
            assert stat == 0, "umount nfs client failed."
            stat, _ = self.sshclient.ssh_exec(self.mount_nfs)
            assert stat == 0, "Nfs client mount failed."

        finally:
            #验证节点是否ping 通
            time.sleep(10)
            #ping验证
            for i in range(60):
                stat = ping_test(dns_master_ip)
                if not stat:
                    time.sleep(10)
                else:
                    break
            else:
                raise AssertionError("HOST unreachable.")
            # self.sshclient.ssh_exec("killall -9 vdbench")
            self.sshclient.ssh_exec("ps axu|grep vdbench|awk '{print $2}'|xargs -I {} kill -9 {}")
            self.sshclient.ssh_exec("umount " + self.mountdir)
            check_cluster_health()