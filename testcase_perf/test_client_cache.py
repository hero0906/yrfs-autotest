#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Desciption : client cache perfmance
@Time : 2021/11/09 11:58
@Author : caoyi
"""

import os
import logging
import time
from time import sleep
from config import consts
from common.util import sshClient
from depend.client import client_mount, run_vdbench
from depend.perftest import vdbench_test, fio_test

logger = logging.getLogger(__name__)


class Test_clientCache:

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.sshclient = sshClient(self.clientip)
        self.testpath = os.path.join(consts.MOUNT_DIR, "autotest_client_cache_" + time.strftime("%m-%d-%H%M%S"))
        # 客户端挂载
        mount_stat = client_mount(self.clientip, acl_add=True, param="client_cache_type = cache")
        assert mount_stat == 0, "client mount failed."
        # 创建测试目录
        self.sshclient.ssh_exec("mkdir -p " + self.testpath)
        self.sshclient.ssh_exec("mkdir -p %s/dir1" % self.testpath)

    def teardown_class(self):
        self.sshclient.ssh_exec("rm -fr " + self.testpath)
        self.sshclient.close_connect()

    def test_cache_perf(self):
        """
        客户端缓存：2245 内存击穿，性能下降不超过20%
        """
        # 客户端的基准测试
        self.sshclient.ssh_exec("sync;echo 3 > /proc/sys/vm/drop_caches")
        vd_init_res = vdbench_test(self.clientip, self.testpath, report_path="/tmp/autotest_fio_cache_before",
                                   sync=False)
        fio_init_res = fio_test(self.clientip, self.testpath, report_path="/tmp/autotest_fio_cache_before", sync=False)
        init_res = list(vd_init_res.values()) + list(fio_init_res.values())
        # 执行业务填充cache
        vdstat = run_vdbench(self.testpath + "/dir1")
        assert vdstat == 0, "vdbench run failed."
        # 检测客户端的cache占用量
        while True:
            _, cache = self.sshclient.ssh_exec("free -m | sed -n '2p' | awk '{{print $3/$2*100}}'")
            if float(cache) > 20:
                break
            else:
                #logger.info("Mem cache percent %s%%" % cache)
                sleep(10)
        # 再次测试性能值
        self.sshclient.ssh_exec("killall -9 java")
        sleep(2)
        vd_end_res = vdbench_test(self.clientip, self.testpath, report_path="/tmp/autotest_vdbench_cache_after",
                                  sync=False)
        fio_end_res = fio_test(self.clientip, self.testpath, report_path="/tmp/autotest_vdbench_cache_after",
                               sync=False)
        end_res = list(vd_end_res.values()) + list(fio_end_res.values())
        logger.info("Please check test log:\n"
                    "FIO:/tmp/autotest_fio_cache_before,/tmp/autotest_fio_cache_after\n"
                    "Vdbench:/tmp/autotest_fio_cache_before,/tmp/autotest_vdbench_cache_after")
        # 检验性能损耗小于百分之二十
        for n, m in zip(init_res, end_res):
            logger.info("Init perfmance: %s,High cache usage perfmance: %s." % (str(n), str(m)))
            assert int(n) * 0.8 < int(m), "Performance loss is greater than 20%"
