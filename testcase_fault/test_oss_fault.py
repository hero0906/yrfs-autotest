# coding=utf-8
'''
@Desciption : oss fault test
@Time : 2021/03/19 10:27
@Author : caoyi
'''

import os
import pytest
import logging
from time import sleep
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from common.cluster import get_osd_master, check_cluster_health

logger = logging.getLogger(__name__)

@pytest.mark.faultTest
class Test_ossFault(YrfsCli):

    def test_unlink_fault(self):
        '''
        bugID: 4150 【6.5.6】 close file(unlink disposal) => unlink chunk failed触发meta恢复
        '''
        self.serverip = consts.META1
        try:
            # 测试文件准备
            check_cluster_health()
            sshserver = sshClient(self.serverip)
            testfile = "autotest_unlink"
            testpath = os.path.join(consts.MOUNT_DIR, testfile)

            sshserver.ssh_exec("dd if=/dev/zero of=%s bs=4k count=1" % testpath)
            test_script = "echo -e \"import os\nf=open('{0}','r')\nos.unlink('{0}')\nf.close()\" >> /tmp/autotest.py".format(testpath)
            #获取文件的oss master节点ip
            master_oss_node = get_osd_master(testfile)[0]
            #执行python脚本
            logger.info("Run /tmp/autotest.py fault script.")
            sshserver.ssh_exec(test_script)
            sshserver.ssh_exec("python /tmp/autotest.py")
            #kill oss master节点的服务。
            sshmaster = sshClient(master_oss_node)

            oss_service_name = self.get_cli("oss_service")
            logger.info("Kill node %s oss service" % master_oss_node)
            sshmaster.ssh_exec("ps axu|grep " + oss_service_name + "|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
            #检车此时的meta状态是否正常
            mds_cmd = self.get_cli("mds_map") + "|awk 'NR>1'|grep -v up/clean"
            for loop in range(3):
                mds_stat, _ = sshserver.ssh_exec(mds_cmd)
                assert mds_stat != 0, "mds stat not up/clean."
                sleep(2)
            sleep(5)
            logger.info("Start node %s oss service" % master_oss_node)
            for loop in range(10):
                for i in range(3):
                    start_osd_stat, _ = sshmaster.ssh_exec("systemctl start " + oss_service_name)
                    sleep(5)
                if start_osd_stat == 0:
                    break
                else:
                    sleep(2)
                    continue
            assert start_osd_stat == 0, "storage service start failed."
            #查看集群状态，直至返回正常
        finally:
            sshserver.ssh_exec("rm -fr " + testpath)
            sshserver.ssh_exec("rm -fr /tmp/autotest.py")
            sshmaster.ssh_exec("systemctl start " + oss_service_name)
            sshserver.close_connect()
            sshmaster.close_connect()
            check_cluster_health()