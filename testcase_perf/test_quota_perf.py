#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : nonempty dir quota perfamance test
@Time : 2021/11/19 11:50
@Author : caoyi
"""
import time
import logging
from time import sleep
from config import consts
from common.util import sshClient
from depend.client import client_mount
from depend.perftest import fio_test
from common.cli import YrfsCli

logger = logging.getLogger(__name__)


class Test_quotaPerf(YrfsCli):

    def test_set_perf(self):
        """
        3684 （非空目录quota）目录中存在大量文件设置过程中，读写quota目录性能损耗情况。
        """
        testdir = "autotest_quota_perf_" + time.strftime("%m-%d-%H%M%S")
        testpath = consts.MOUNT_DIR + "/" + testdir
        serverip = consts.META1
        clientip = consts.CLIENT[0]
        sshserver = sshClient(serverip)
        sshclient = sshClient(clientip)
        try:
            #创建测试文件
            sshserver.ssh_exec("mkdir -p " + testpath)
            #客户端挂载
            stat = client_mount(clientip, acl_add=True)
            assert stat == 0,"Expect: client mount success."
            #mdtest 数据填充
            sshclient.ssh_exec("mdtest -C -d %s/dir1 -i 1 -w 0 -I 40000 -z 1 -b 10 -L -F" % testpath)
            #fio测试基准性能
            init_perf = fio_test(clientip, testpath)
            #设置quota过程中
            sshserver.ssh_exec(self.get_cli("nquota_add", testdir, "200G", "1500000") + " &")
            sleep(2)
            end_perf = fio_test(clientip, testpath)
            #对比性能差异小于10%
            for m,n in zip(init_perf.values(), end_perf.values()):
                logger.info("Init perfmance: %s, End perfmance : %s." % (str(m), str(n)))
                assert int(m) * 0.8 < int(n), "Expect: Performance loss less than 10 percent"
        finally:
            sshserver.ssh_exec("ps axu|grep -v grep|grep projectquota|awk '{print $2}'|xargs -I {} kill -9 {}")
            sshserver.ssh_exec("mkdir -p {0};rsync -apgolr --delete {0} {1}/".format("/autotest_rsync/", testpath))
            sshserver.ssh_exec(self.get_cli("quota_remove", testdir))
            sshserver.ssh_exec("rm -fr " + testpath)
            sshserver.close_connect()
            sshclient.close_connect()


