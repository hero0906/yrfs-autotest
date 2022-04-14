#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : meta rebuild test suite
@Time : 2021/11/05 15:13
@Author : caoyi
"""

import os
import pytest
import time
import logging
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount
from common.cluster import check_cluster_health, get_mds_master

logger = logging.getLogger(__name__)

@pytest.mark.funcTest
class Test_metaRebuild(YrfsCli):

    def setup_class(self):
        serverip = consts.META1
        clientip = consts.CLIENT[0]

        self.sshclient = sshClient(clientip)
        self.sshserver = sshClient(serverip)
        self.testdir = "autotest_meta_rebuild_" + time.strftime("%m-%d-%H%M%S")
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)

        self.recover_cmd = self.get_cli(self, "recover_meta")
        #客户端挂载
        self.sshserver.ssh_exec("rm -fr {0};mkdir -p {0}/dir{{1..2}}".format(self.testpath))
        #获取目录的当前mds group组id
        self.groupid, _ = get_mds_master(self.testdir)
        #其他mds组id
        _, allgroup = self.sshserver.ssh_exec("yrcli --group --type=mds|awk 'NR>1{print $1}'")
        allgroup = allgroup.split("\n")
        for i in allgroup:
            if i != self.groupid:
                self.othergroup = i
                logger.info("Non-negative MDS group id: %s" % self.othergroup)
                break
        #客户端挂载
        mountstat = client_mount(clientip, acl_add=True)
        if mountstat != 0:
            pytest.skip(msg="client mount failed", allow_module_level=True)
        #填充测试文件
        self.mdtest = "mdtest -C -d {0} -i 1 -w 0 -I 100000 -z 1 -b 1 -L -F"
        mdstat, mdres = self.sshclient.ssh_exec(self.mdtest.format(self.testpath + "/dir1"))
        assert mdstat == 0, "mdtest test failed."
        self.init_perf = float(mdres.split("\n")[13].split()[3])
        logger.info("Mdtest init perfmanece: %s " % self.init_perf)

        self.sshserver.ssh_exec("mkdir -p /autotest_rsync")

    def teardown_class(self):
        #目录清理工作
        self.sshserver.ssh_exec("rsync -apgolr --delete /autotest_rsync/ {0}/;rm -fr {0}".format(self.testpath))
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    @pytest.mark.parametrize("threadnum", ("normal", "6", "48"))
    @pytest.mark.parametrize("group", ("aff", "noaff"))
    @pytest.mark.parametrize("point", ("before", "after"))
    def test_change_threads(self, threadnum, group, point):
        """
        2094 校验从节点resyncing状态，修改value线程（12->6）是否有效(不同线程数、是否属组关系、rebuild前后设置)
        """
        #2099 校验从节点good状态，默认value（为12）执行mdtest是否有影响
        #查看当前的线程数
        current_num = ""
        try:
            stat, current_num = self.sshserver.ssh_exec(self.get_cli("get_config", "nr_threads_treesync") + \
                                            "|tail -n 1|awk '{print $4}'")
            assert stat == 0, "get config failed."
            #换算当前所属组
            if group == "aff":
                groupid = self.groupid
            else:
                groupid = self.othergroup
            #执行rebuild
            if point == "before":
                self.sshserver.ssh_exec(self.recover_cmd.format(groupid))
            #设置线程数
            if threadnum != "normal":
                stat, _ = self.sshserver.ssh_exec(self.get_cli("set_config", "nr_threads_treesync", threadnum))
                assert stat == 0, "set config failed."
            #执行rebuild
            if point == "after":
                self.sshserver.ssh_exec(self.recover_cmd.format(groupid))
            #再次性能测试
            stat, res = self.sshclient.ssh_exec(self.mdtest.format(self.testpath + "/dir2"))
            assert stat == 0,"mdtest failed."
            perf_tmp = float(res.split("\n")[13].split()[3])
            perf = perf_tmp * 1.2
            logger.info("Performance value after reconstruction: %s" % perf)
            #对比性能值
            if group == "aff":
                #归属组性能损耗小于百分之20
                assert self.init_perf < perf, "Performance loss is greater than 20%"
            else:
                #非归属组性能无损耗
                assert self.init_perf * 0.9 < perf_tmp < self.init_perf * 1.1, "Expect:Non-owning group \
                            performance has no loss"
        finally:
            self.sshserver.ssh_exec(self.get_cli("set_config", "nr_threads_treesync", current_num))
            self.sshserver.ssh_exec("rsync -apgolr --delete /autotest_rsync/ {0}/".format(self.testpath + "/dir2"))
            check_cluster_health()