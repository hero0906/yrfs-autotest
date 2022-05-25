# coding=utf-8
"""
@Desciption : qos function case
@Time : 2020/12/25 11:13
@Author : caoyi
"""

import pytest
import os
import re
from time import sleep
import logging
import time
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount, run_fstest

logger = logging.getLogger(__name__)


# @pytest.mark.skip
@pytest.mark.funcTest
class Test_QosFunc(YrfsCli):
    '''
    单客户端qos功能测试case集合
    '''

    def setup_class(self):
        # 设置变量

        self.client = consts.CLIENT[0]
        self.server = consts.META1
        self.iops = 100
        self.bps = "10M"
        self.mops = 0
        self.testdir = "autotest_qos_" + time.strftime("%m-%d-%H%M%S")
        self.aclid = "autotest"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.fio = "fio -iodepth=16 -numjobs=1 -size=10M -ramp_time=0 -time_based -runtime=30 -ioengine=psync " + \
                   "-group_reporting -name=test -per_job_logs=0 -log_avg_msec=1000 -write_bw_log=/tmp/autotest " + \
                   "-write_iops_log=/tmp/autotest -filename=%s/autotest_file " % consts.MOUNT_DIR

        self.fio_iops_log = "/tmp/autotest_iops.log"
        self.fio_bw_log = "/tmp/autotest_bw.log"
        self.sshserver = sshClient(self.server)
        self.sshclient = sshClient(self.client)

        # 有可能之前失败用例残留fio log导致失败，所以提前删除下fio log
        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        # 类预制条件客户端，挂载客户端
        _fio_stat, _ = self.sshclient.ssh_exec("fio --version")
        if _fio_stat != 0:
            pytest.skip(msg="skip beause fio not installed", allow_module_level=True)

        self.sshserver.ssh_exec('mkdir ' + self.testpath)
        sleep(2)
        acl_add_cmd = self.get_cli(self, 'acl_id_add', self.testdir, self.aclid, "rw")
        self.sshserver.ssh_exec(acl_add_cmd)
        _status = client_mount(self.client, self.testdir, aclid=self.aclid)
        # 判断客户端是否挂载成功，挂载失败跳过所有用例。
        if _status != 0:
            self.sshserver.ssh_exec('rm -fr ' + self.testpath)
            pytest.skip(msg="skip beause client mount failed", allow_module_level=True)

    def teardown_class(self):
        self.sshserver.ssh_exec(self.get_cli(self, "qos_remove", self.testdir))
        acl_del_cmd = self.get_cli(self, 'acl_id_del', self.testdir, self.aclid)
        self.sshserver.ssh_exec(acl_del_cmd)
        self.sshserver.ssh_exec('rm -fr ' + self.testpath)

        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def teardown(self):
        self.sshclient.ssh_exec("killall -9 fio")

    def test_total_qos_iops_write(self):
        '''
        caseID:3090 设置总qos write iops测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_total_qos_iops_read(self):
        '''
        caseID:3090 设置总qos read iops测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4K")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_total_qos_bw_write(self):
        '''
        caseID: 3090 设置总qos写带宽测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_total_qos_bw_read(self):
        '''
        caseID: 3090 设置总qos 读带宽测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_qos_mops(self):
        '''
        caseID: 3090 设置总qos mops测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, '0', '0', '10'))
        sleep(10)
        stat, res = self.sshclient.ssh_exec('time touch %s/autotest_qos_file{1..20}' % consts.MOUNT_DIR)
        times = re.findall(r'\t*m([0-9])', res)[0]
        assert int(times) >= 5, "qos mops exceed"

    def test_part_qos_iops_write(self):
        '''
        caseID:3090 单独设置qos write iops测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_part_qos_iops_read(self):
        '''
        caseID:3090 单独设置qos read iops测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_part_qos_bw_write(self):
        '''
        caseID: 3090 单独设置qos写带宽测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_part_qos_bw_read(self):
        '''
        # caseID: 3090 单独设置qos写带宽测试
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_set_part_iops(self):
        '''
        caseID: 3078 对正在进行读业务的目录设置单独qos
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(10)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_set_part_iops(self):
        """
        caseID: 3078 对正在进行读业务的目录设置单独qos iops
        """
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4K &")
        sleep(10)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_set_part_bw(self):
        '''
        caseID: 3078 对正在进行度业务的目录设置单独qos 写带宽测试
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_set_part_bw(self):
        '''
        caseID: 3078 对正在进行度业务的目录设置单独qos 读带宽测试
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_set_total_iops(self):
        '''
        caseID: 3078 对正在进行写业务的目录设置单独qos iops测试
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_set_total_iops(self):
        '''
        caseID: 3078 对正在进行读业务的目录设置单独qos iops测试
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4K &")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_set_total_bw(self):
        '''
        caseID: 3078 对正在进行写业务的目录设置单独qos 带宽测试
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_set_total_bw(self):
        '''
        caseID: 3078 对正在进行写业务的目录设置单独qos bps
        '''
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_del_part_iops(self):
        '''
        caseID: 3081 对正在进行写iops已单独设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if iops < int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_del_part_iops(self):
        '''
        caseID: 3081 对正在进行读iops已单独设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4K&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if iops < int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_del_part_bw(self):
        '''
        caseID: 3081 对正在进行写带宽已单独设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if bw < int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_del_part_bw(self):
        '''
        caseID: 3081 对正在进行读带宽已单独设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if bw < int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    # 以下为测试写数据过程中，删除qos设置。
    def test_writing_del_total_iops(self):
        '''
        # caseID: 3081 对正在进行写iops已统一设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if iops < int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_del_total_iops(self):
        '''
        # caseID: 3081 对正在进行读iops已统一设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4K&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if iops < int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_writing_del_total_bw(self):
        '''
        # caseID: 3081 对正在进行写带宽已统一设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if bw < int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_reading_del_total_bw(self):
        '''
        # caseID: 3081 对正在进行读带宽已统一设置qos的目录取消qos设置
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        # sleep(10)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M&")
        sleep(10)
        self.sshserver.ssh_exec(self.get_cli('qos_remove', self.testdir))
        sleep(40)
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if bw < int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_riops(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数riops
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "riops", "100"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4k")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_wiops(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数wiops
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "wiops", "100"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4k")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_tiops(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数tiops
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "tiops", "100"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=4k")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_rbps(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数rbps
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "rbps", "10M"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=read -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_wbps(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数wbps
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "wbps", "10M"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_tbps(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数tbps
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "tbps", "10M"))
        sleep(5)
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=1M")
        stat, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        exceed_num = 0
        for bw in res.split("\n"):
            bw = int(int(bw) / 1024)
            bps = int(self.bps[:-1])
            if 0 > bw or bw > int(bps + bps / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_single_mops(self):
        '''
        caseID: 3064 命令行添加qos，只选择一项参数tbps
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli("qos_single_set", self.testdir, "mops", "10"))
        sleep(5)
        stat, res = self.sshclient.ssh_exec('time touch %s/autotest_qos_file{1..20}' % consts.MOUNT_DIR)
        times = re.findall(r'\t*m([0-9])', res)[0]
        assert stat == 0, "touch file failed."
        assert int(times) >= 5, "qos mops exceed."

    @pytest.mark.parametrize("settype", ("total", "alone"))
    @pytest.mark.parametrize("limit", ("bps", "iops"))
    @pytest.mark.parametrize("rw", ("read", "write"))
    @pytest.mark.parametrize("turn", ("up", "down"))
    def test_adjust_qos(self, limit, rw, settype, turn):
        '''
        caseID: 3079 已设置综合qos限制的目录在单客户端读写时，调大、调小iops bps限制正确
        '''
        # caseID: 3080 已设置综合qos限制的目录在单客户端读写时，调小qos iops
        sleep(5)
        try:
            # 设置qos目录数值，运行fio业务
            if turn == "up":
                # 调大验证测试
                if settype == "total":
                    self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, "5M", "50", self.mops))
                else:
                    self.sshserver.ssh_exec(
                        self.get_cli('qos_part_set', self.testdir, "5M", "5M", "50", "50", self.mops))
            else:
                # 调小验证测试
                if settype == "total":
                    self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, "50M", "400", self.mops))
                else:
                    self.sshserver.ssh_exec(
                        self.get_cli('qos_part_set', self.testdir, "50M", "50M", "500", "500", self.mops))
            # iops还是带宽测试
            if limit == "iops":
                self.sshclient.ssh_exec(self.fio + "-rw=%s -bs=4K &" % rw)
            else:
                self.sshclient.ssh_exec(self.fio + "-rw=%s -bs=1M &" % rw)
            sleep(5)
            # 增大qos数值
            if limit == "bps":
                self.iops = 1000000
            else:
                self.bps = "500G"
            if settype == "total":
                add_stat, _ = self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops,
                                                                   self.mops))
            else:
                add_stat, _ = self.sshserver.ssh_exec(self.get_cli('qos_part_set', self.testdir, self.bps, self.bps,
                                                                   self.iops, self.iops, self.mops))
            assert add_stat == 0, "add qos failed."
            logger.info("sleep 40s.")
            sleep(40)
            exceed_num = 0
            if limit == "iops":
                stat_log, iops_res = self.sshclient.ssh_exec(
                    "cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
                assert stat_log == 0, "Cann't find fio log file"
                for iops in iops_res.split("\n"):
                    iops = int(iops)
                    if 0 > iops or iops > int(self.iops + self.iops / 10):
                        exceed_num += 1
            else:
                stat_log, bps_res = self.sshclient.ssh_exec(
                    "cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
                assert stat_log == 0, "Cann't find fio log file"
                for bw in bps_res.split("\n"):
                    bw = int(int(bw) / 1024)
                    bps = int(self.bps[:-1])
                    if 0 > bw or bw > int(bps + bps / 10):
                        exceed_num += 1
            assert exceed_num == 0, "Qos exceeds the limit"
        finally:
            self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))

    def test_turn_down(self):
        '''
        caseID: 3080 已设置综合qos限制的目录在单客户端读写时，调小qos iops
        '''
        sleep(5)
        # 设置qos目录数值，运行fio业务
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, "20M", "400", self.mops))
        self.sshclient.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(5)
        # 增大qos数值
        add_stat, _ = self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        assert add_stat == 0, "add qos failed."
        logger.info("sleep 40s.")
        sleep(40)
        # 检查log的正确性是否存在超过预期数值+-10%的情况
        stat_log, res = self.sshclient.ssh_exec("cat %s |awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        exceed_num = 0
        for iops in res.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        self.sshclient.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        assert stat_log == 0, "cann't find fio log file"
        assert exceed_num == 0, "qos exceed the default value"

    def test_qos_posix(self):
        """
        3139 配置了qos的目录下进行posix基本io测试
        """
        sleep(5)
        # 设置qos目录数值
        add_stat, _ = self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        assert add_stat == 0, "add qos failed."
        # 执行fstest检查
        run_fstest(self.client, consts.MOUNT_DIR)


# @pytest.mark.skip(msg="expect skip,not run two client")
@pytest.mark.funcTest
class Test_twoClientFunc(YrfsCli):
    '''
        多客户端qos功能测试case集合
        '''

    def setup_class(self):
        if len(consts.CLIENT) < 2:
            pytest.skip(msg="skip, need two client", allow_module_level=True)

        self.client1 = consts.CLIENT[0]
        self.client2 = consts.CLIENT[1]
        self.iops = 200
        self.bps = "20M"
        self.mops = 10000
        self.testdir = "autotest_qos"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.aclid = "autotest"
        self.server = consts.META1
        self.testfile = consts.MOUNT_DIR + "/autotest_file"

        self.fio = "fio -iodepth=16 -numjobs=1 -size=2M -ramp_time=0 -time_based -runtime=30 -ioengine=psync " + \
                   "-group_reporting -name=test -per_job_logs=0 -log_avg_msec=1000 -write_bw_log=/tmp/autotest " + \
                   "-write_iops_log=/tmp/autotest -filename=%s " % self.testfile

        # 防止fio准备文件超时，dd提前准备。
        self.dd_cmd = "dd if=/dev/zero of=%s bs=1M count=10" % self.testfile

        self.fio_iops_log = "/tmp/autotest_iops.log"
        self.fio_bw_log = "/tmp/autotest_bw.log"

        self.sshserver = sshClient(self.server)
        self.sshclient1 = sshClient(self.client1)
        self.sshclient2 = sshClient(self.client2)
        # 清除测试客户端可能潜在的log日志
        self.sshclient1.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        self.sshclient1.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        # 校验客户端fio版本是否存在
        _fio_version1, _ = self.sshclient1.ssh_exec("fio --version")
        _fio_version2, _ = self.sshclient2.ssh_exec("fio --version")
        if _fio_version1 != 0 or _fio_version2 != 0:
            pytest.skip(msg="skip, fio not install", allow_module_level=True)
        # 创建测试目录并且添加acl mount权限
        self.sshserver.ssh_exec('mkdir ' + self.testpath)
        sleep(2)
        acl_add_cmd = self.get_cli(self, 'acl_id_add', self.testdir, self.aclid, "rw")
        self.sshserver.ssh_exec(acl_add_cmd)

        _mount_stat1 = client_mount(self.client1, self.testdir, aclid=self.aclid)
        _mount_stat2 = client_mount(self.client2, self.testdir, aclid=self.aclid)
        if _mount_stat1 != 0 or _mount_stat2 != 0:
            self.sshserver.ssh_exec('rm -fr ' + self.testpath)
            pytest.skip(msg="skip, client mount failed", allow_module_level=True)

    def teardown_class(self):
        # 清理测试数据
        self.sshserver.ssh_exec(self.get_cli(self, "qos_remove", self.testdir))
        acl_del_cmd = self.get_cli(self, 'acl_id_del', self.testdir, self.aclid)
        self.sshserver.ssh_exec(acl_del_cmd)
        self.sshserver.ssh_exec('rm -fr ' + self.testpath)

        self.sshserver.close_connect()
        self.sshclient1.close_connect()
        self.sshclient2.close_connect()

    def setup(self):
        self.sshclient1.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        self.sshclient2.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))

    def teardown(self):
        self.sshclient1.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))
        self.sshclient2.ssh_exec("rm -fr %s %s" % (self.fio_iops_log, self.fio_bw_log))

    def test_total_qos_iops_write(self):
        '''
            caseID: 3082 测试两个客户端统一设置qos，iops写设置符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(10)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_total_qos_iops_read(self):
        '''
        caseID: 3082 测试两个客户端total设置qos，iops读设置符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        _, dd_res = self.sshclient1.ssh_exec(self.dd_cmd)
        sleep(1)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert "copied" in dd_res, "dd failed."
        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    # @pytest.mark.skip(reason="Not. finished")
    def test_del_qos(self):
        '''
            caseID: 3086 （自动化）已设置qos信息的目录在多个客户端读写时，删除qos
            '''
        sleep(5)
        add_stat, _ = self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        assert add_stat == 0, "add qos failed."
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(5)
        # 删除qos设置
        del_stat, _ = self.sshserver.ssh_exec(self.get_cli("qos_remove", self.testdir))
        assert del_stat == 0, "del qos failed"
        sleep(50)
        # 查看log情况
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        # 收集qos信息
        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        # 两个节点要除以2
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if iops < limit_iops:
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    @pytest.mark.parametrize("turn", ("up", "down"))
    def test_twoclient_turn(self, turn):
        '''
        3085 （自动化）已设置qos信息的目录在多个客户端读写时，调小、调大qos
        '''
        sleep(5)
        if turn == "up":
            add_stat, _ = self.sshserver.ssh_exec(
                self.get_cli('qos_total_set', self.testdir, self.bps, "10", self.mops))
            assert add_stat == 0, "Add qos failed."
        else:
            add_stat, _ = self.sshserver.ssh_exec(
                self.get_cli('qos_total_set', self.testdir, self.bps, self.iops * 2, self.mops))
            assert add_stat == 0, "Add qos failed."

        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(5)
        # 缩小iops数值
        update_stat, _ = self.sshserver.ssh_exec(
            self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        assert update_stat == 0, "update qos failed"
        logger.info("sleep 50s")
        sleep(50)
        # 查看log情况
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        # 收集qos信息
        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_iops_mix(self):
        '''
            # caseID: 3082 测试两个客户端一个读iops一个写iops，qos limit限制符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_total_qos_bps_write(self):
        '''
        caseID: 3082 测试两个客户端total设置qos，iops写设置符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=1M &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_bps = int(int(self.bps[:-1]) * 1024 / 2)

        for bps in res:
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_total_qos_bps_read(self):
        '''
            caseID: 3082 测试两个客户端total设置qos，bps读设置符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=1M &")
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_bps = int(int(self.bps[:-1]) * 1024 / 2)

        for bps in res:
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_bps_mixrw(self):
        '''
        caseID: 3082 测试两个客户端一个设置读bps一个设置写bps，qos limit符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=1M &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_bps = int(int(self.bps[:-1]) * 1024 / 2)

        for bps in res:
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_iops_mixrw(self):
        '''
        caseID: 3082 测试两个客户端一个读iops一个写iops，qos limit限制符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        _, dd_res = self.sshclient1.ssh_exec(self.dd_cmd)
        sleep(1)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if 0 > iops or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert "copied" in dd_res, "dd failed."
        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    @pytest.mark.skip
    def test_twolient_mops(self):
        '''
        caseID: 3082 两个客户端设置qos mops测试
        '''
        try:
            sleep(5)
            self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, '0', '0', '20'))
            sleep(10)
            self.sshclient1.ssh_exec(r"(time touch %s/autotest_qos1_file{1..40}) > /tmp/autotest_mops.log 2>&1 &"
                                     % consts.MOUNT_DIR)
            self.sshclient2.ssh_exec(r"(time touch %s/autotest_qos2_file{1..40}) > /tmp/autotest_mops.log 2>&1"
                                     % consts.MOUNT_DIR)
            sleep(60)
            _, res1 = self.sshclient1.ssh_exec(r"cat /tmp/autotest_mops.log|grep real|awk '{print $2}'")
            _, res2 = self.sshclient2.ssh_exec(r"cat /tmp/autotest_mops.log|grep real|awk '{print $2}'")

            times1 = re.findall(r'm([0-9]*).', res1)
            logger.info("client1: %s touch file elapsed time %ss" % (self.client1, res1))
            times2 = re.findall(r'm([0-9]*).', res2)
            logger.info("client1: %s touch file elapsed time %ss" % (self.client2, res2))

        finally:

            self.sshclient1.ssh_exec('rm -fr /tmp/autotest_mops.log')
            self.sshclient2.ssh_exec('rm -fr /tmp/autotest_mops.log')

        assert int(''.join(times1)) >= 10 and int(''.join(times2)) >= 10, "ops not meet expectations."

    def test_part_qos_iops_write(self):
        '''
            caseID: 3082 测试两个客户端单独设置qos，iops写设置符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if 0 > iops or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_part_qos_iops_read(self):
        '''
        caseID: 3082 测试两个客户端单独设置qos，iops读设置符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_iops = int(self.iops / 2)

        for iops in res:
            iops = int(iops)
            if 0 > iops or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_part_qos_bps_write(self):
        '''
        caseID: 3082 测试两个客户端单独设置qos，iops写设置符合预期
        '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=1M &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_bps = int(int(self.bps[:-1]) * 1024 / 2)

        for bps in res:
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_part_qos_bps_read(self):
        '''
            # caseID: 3082 测试两个客户端单独设置qos，bps读设置符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=1M &")
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0
        res = res1.split("\n") + res2.split("\n")
        limit_bps = int(int(self.bps[:-1]) * 1024 / 2)

        for bps in res:
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_write_mixbs(self):
        '''
            caseID: 3087 两个客户端4K、1M混合块写，qos limit限制符合预期,并且能够平稳输出。
            '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0

        limit_bps = int(int(self.bps[:-1]) * 1024)
        limit_iops = self.iops - int(self.bps[:-1])

        for iops in res1.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        for bps in res2.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_read_mixbs(self):
        '''
            caseID: 3087 两个客户端4K、1M混合块读，qos limit限制符合预期
            '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0

        limit_bps = int(int(self.bps[:-1]) * 1024)
        limit_iops = self.iops - int(self.bps[:-1])

        for iops in res1.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(limit_iops + limit_iops / 10):
                exceed_num += 1

        for bps in res2.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(limit_bps + limit_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_write_iops_unequal(self):
        '''
            # caseID: 3087 多个客户端写iops测试，客户端业务不等时按照负载自动分配
            '''
        low_iops = int(self.iops * (1 / 4))
        high_iops = self.iops - low_iops

        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=4k -rate_iops={iops},{iops} &".format(iops=low_iops))
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0

        for iops in res1.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(low_iops + low_iops / 10):
                exceed_num += 1
        for iops in res2.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(high_iops + high_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_read_iops_unequal(self):
        '''
            # caseID: 3087 多个客户端写iops测试，客户端业务不等时按照负载自动分配
            '''
        low_iops = int(self.iops * (1 / 4))
        high_iops = self.iops - low_iops

        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=read -bs=4k -rate_iops={iops},{iops} &".format(iops=low_iops))
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=4K &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0

        for iops in res1.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(low_iops + low_iops / 10):
                exceed_num += 1
        for iops in res2.split("\n"):
            iops = int(iops)
            if iops < 0 or iops > int(high_iops + high_iops / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_write_bps_unequal(self):
        '''
            # caseID: 3087 多个客户端写带宽测试，客户端业务不等时按照负载自动分配
            '''
        low_bps = int(int(self.bps[:-1]) * (1 / 4) * 1024)
        high_bps = int(int(self.bps[:-1]) * (3 / 4) * 1024)

        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=1M -rate_iops={bps},{bps} &".format(bps=low_bps / 1024))
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0

        for bps in res1.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(low_bps + low_bps / 10):
                exceed_num += 1
        for bps in res2.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(high_bps + high_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_read_bps_unequal(self):
        '''
            # caseID: 3087 多个客户端读带宽测试，客户端业务不等时按照负载自动分配
            '''
        low_bps = int(int(self.bps[:-1]) * (1 / 4) * 1024)
        high_bps = int(int(self.bps[:-1]) * (3 / 4) * 1024)

        sleep(5)
        self.sshserver.ssh_exec(self.get_cli('qos_total_set', self.testdir, self.bps, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(
            self.fio + "-rw=read -bs=1M -rate_iops={bps},{bps} &".format(bps=low_bps / 1024))
        self.sshclient2.ssh_exec(self.fio + "-rw=read -bs=1M &")
        sleep(50)
        stat1, res1 = self.sshclient1.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)
        stat2, res2 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_bw_log)

        exceed_num = 0

        for bps in res1.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(low_bps + low_bps / 10):
                exceed_num += 1
        for bps in res2.split("\n"):
            bps = int(bps)
            if bps < 0 or bps > int(high_bps + high_bps / 10):
                exceed_num += 1

        assert stat1 == 0 and stat2 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"

    def test_twoclient_drop_oneclient(self):
        '''
            caseID: 3089 两个客户端qos目录write过程中，暂停其中一个客户端业务，另一个客户端qos值会随之增大。
            '''
        sleep(5)
        self.sshserver.ssh_exec(
            self.get_cli('qos_part_set', self.testdir, self.bps, self.bps, self.iops, self.iops, self.mops))
        sleep(5)
        self.sshclient1.ssh_exec(self.fio + "-rw=write -bs=4k &")
        self.sshclient2.ssh_exec(self.fio + "-rw=write -bs=4K &")
        sleep(10)
        self.sshclient1.ssh_exec("ps axu|grep fio|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
        sleep(40)
        stat1, res1 = self.sshclient2.ssh_exec("cat %s|awk -F ', ' '{print $2}'|tail -n +20" % self.fio_iops_log)

        exceed_num = 0

        for iops in res1.split("\n"):
            iops = int(iops)
            if 0 > iops or iops > int(self.iops + self.iops / 10):
                exceed_num += 1

        assert stat1 == 0, "not found fio log file"
        assert exceed_num == 0, "qos exceed default value"
