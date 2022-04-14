#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : qos dir perfmance
@Time : 2021/11/26 15:00
@Author : caoyi
"""
import pytest
import time
from common.cli import YrfsCli
from common.cluster import check_cluster_health
from common.fault import makeFault
from common.util import sshClient
from config import consts
from depend.client import client_mount


class Test_qosFault(YrfsCli):
    def setup(self):
        self.makefault = makeFault()

    @pytest.mark.parametrize("node", ("slave", "master"))
    @pytest.mark.parametrize("faulttype", ("kill", "reboot"))
    def test_fault_mgr(self, node, faulttype):
        """
        3094 配置qos的目录读写过程中，mgmt主发生故障
        """
        testdir = "autotest_qos_fault_" + time.strftime("%m-%d-%H%M%S")
        mountdir = consts.MOUNT_DIR
        client = consts.CLIENT[0]
        server = consts.META1
        fio_log = "/tmp/autotest_iops.log"
        fiocmd = "fio -iodepth=16 -numjobs=1 -size=10M -ramp_time=5 -time_based -runtime=30 -ioengine=psync " + \
                 "-group_reporting -name=test -per_job_logs=0 -log_avg_msec=1000 -bs=4K " + \
                 "-write_iops_log=/tmp/autotest -filename=%s/autotest_file -rw=write &" % mountdir
        # ssh session
        sshserver = sshClient(server)
        sshclient = sshClient(client)
        try:
            # 删除log
            sshclient.ssh_exec("rm -fr %s" % fio_log)
            # 创建qos
            sshserver.ssh_exec("cd %s&&mkdir -p %s" % (mountdir, testdir))
            sshserver.ssh_exec(self.get_cli('qos_total_set', testdir, "500M", "100", "0"))
            # 客户端挂载
            stat = client_mount(client, testdir, acl_add=True)
            assert stat == 0, "Client mount failed."
            # fio 数据写入
            sshclient.ssh_exec(fiocmd)
            # 制造mgr故障
            if node == "master":
                if faulttype == "kill":
                    self.makefault.kill_mgr(check=False, master=True)
                else:
                    self.makefault.reboot_mgr(check=False, crash_cmd="reboot -f", master=False)
            else:
                if faulttype == "kill":
                    self.makefault.kill_mgr(check=False, master=True)
                else:
                    self.makefault.reboot_mgr(check=False, crash_cmd="reboot -f", master=False)
            # 检查qos正常
            time.sleep(40)
            stat, res = sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % fio_log)
            assert stat == 0, "Not found fio log."
            #检验数值是否符合预期
            exceed_num = 0
            for iops in res.split("\n"):
                iops = int(iops)
                if iops < int(100 - 100 / 10) or iops > int(100 + 100 / 10):
                    exceed_num += 1
            assert exceed_num == 0, "The qos value is not expected."
        finally:
            # 删除qos配置
            sshserver.ssh_exec(self.get_cli("qos_remove", testdir))
            sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))
            sshclient.ssh_exec("rm -fr " + fio_log)
            time.sleep(10)
            check_cluster_health()
            sshserver.close_connect()
            sshclient.close_connect()
