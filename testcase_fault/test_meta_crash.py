# coding=utf-8
"""
@Desciption : meta steady test
@Time : 2020/02/02 11:13
@Author : caoyi
"""


import pytest
import logging
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.client import client_mount

logger = logging.getLogger(__name__)

@pytest.mark.faultTest
class Test_metaCrash(YrfsCli):
    '''
    稳定性测试case汇总
    '''

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        self.acl_id = "autotestmmap"
        self.testdir = consts.MOUNT_DIR
        self.testfile = self.testdir + "/autotest_mmap_file"

    def teardown_class(self):
        self.sshserver.ssh_exec("rm -fr " + self.testfile)
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_del", "", self.acl_id))
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_fio_mmap(self):
        '''
        bugID:4248 【wanyan】meta crash导致集群异常（客户端跑mmap）
        '''
        # testdir = consts.MOUNT_DIR
        # testfile = testdir + "/autotest_mmap_file"
        # acl_id = "autotest-mmap"
        fio_stat, _ = self.sshclient.ssh_exec("fio --version")
        if fio_stat != 0:
            pytest.skip(msg="not found fio tools test skip.")
        #客户端挂载
        add_acl = self.get_cli("acl_id_add","",self.acl_id,"rw")
        self.sshserver.ssh_exec(add_acl)
        mount_stat = client_mount(self.clientip,aclid=self.acl_id)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed test skip.")
        #客户端数据写入
        fio_cmd = "fio -iodepth=16 -numjobs=4 -size=1G -ramp_time=0 -time_based -runtime=60 -ioengine=mmap " + \
                  "-bs=1m -name=test -filename=%s" % self.testfile
        logger.info(fio_cmd + ", running.")
        fio_stat, _ = self.sshclient.ssh_exec(fio_cmd)
        assert fio_stat == 0, "fio run failed."
        #检查集群状态
        osd_stat, osd_res = self.sshclient.ssh_exec(self.get_cli("mds_map") + "|awk 'NR>1'|grep -v \"up/clean\"")
        mds_stat, mds_res = self.sshclient.ssh_exec(self.get_cli("oss_map") + "|awk 'NR>1'|grep -v \"up/clean\"")
        assert osd_stat != 0 or mds_stat != 0, "osd or mds unhealth."