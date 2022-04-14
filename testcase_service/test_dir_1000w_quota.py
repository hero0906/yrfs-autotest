#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : single dir 1000w
@Time : 2021/11/04 16:13
@Author : caoyi
"""
import os
import pytest
from time import sleep
import logging
import time
from common.util import sshClient
from common.cli import YrfsCli
from config import consts
from depend.client import client_mount
from common.cluster import check_cluster_health, get_mds_master

logger = logging.getLogger(__name__)

#@pytest.mark.skip
@pytest.mark.serviceTest
class Test_tenMillion(YrfsCli):

    def setup_class(self):

        self.recover_cmd = "yrcli --recover --type=mds --groupid={} --restart"

        clientip = consts.CLIENT[0]
        serverip = consts.META1
        self.sshclient = sshClient(clientip)
        self.sshserver = sshClient(serverip)
        self.testdir = "autotest_1000w_" + time.strftime("%m-%d-%H%M%S")
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)

        self.add_quota = self.get_cli(self, "nquota_add")
        self.add_quota_ig = self.get_cli(self, "noquota_add_ignore")
        self.quota_verbose = self.get_cli(self, "quota_list_verbose")
        self.delete_quota = self.get_cli(self, "quota_remove")
        #检查是否存在mdtest测试工具
        mdstat, _ = self.sshclient.ssh_exec("mdtest > /dev/null 2>&1")
        assert mdstat == 0,"not found mdtest tools"
        #客户端挂载
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)
        mountstat = client_mount(clientip, acl_add=True)
        assert mountstat == 0, "client mount failed."

    def teardown_class(self):
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_1000w_file(self):
        """
        3739 使用mdtest创建单目录下1000w文件，并进行元数据操作的测试（quota设置）
        """
        # 3661 （非空目录quota）目录一百万文件设置quota成功
        # 3749 单目录下存在1000w文件，对此目录所属的mds group 触发全量恢复成功
        # 3752 （自动化）单目录下创建1000w子目录后，对此父目录设置quota
        # 3751(自动化) 单目录下创建1000w文件后，对此目录设置quota
        subdir = self.testdir + "/dir1"
        subpath = self.testpath + "/dir1"
        mdtest = "mdtest -C -d %s -i 1 -w 0 -I 10000000 -z 1 -b 1 -L -F" % subpath
        try:
            stat, _ = self.sshclient.ssh_exec(mdtest)
            #此处检验quota设置是否成功
            quotastat, _ = self.sshserver.ssh_exec(self.add_quota.format(subdir, "200G", "15000000"))
            _, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(subdir))
            list_res = list_res_tmp.split("\n")[2].split()
            inodeused = list_res[4]
            assert stat == 0, "mdtest failed."
            assert quotastat == 0, "Expect add quota success."
            assert inodeused == "10000001", "Expect inodeused list correct."
            #再次设置父目录quota
            quotastat, _ = self.sshserver.ssh_exec(self.add_quota_ig.format(self.testdir, "200G", "15000000"))
            _, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            inodeused = list_res[4]
            assert stat == 0, "mdtest failed."
            assert quotastat == 0, "Expect add quota success."
            assert inodeused == "10000002", "Expect inodeused list correct."
            #检查全量恢复是否正常
            #获取mds master group
            groupid, _ = get_mds_master(self.testdir)
            #执行增量恢复
            stat, _ = self.sshserver.ssh_exec(self.recover_cmd.format(groupid))
            assert stat == 0, "Expect recover success"
            check_cluster_health()
            #执行全量恢复
            stat, _ = self.sshserver.ssh_exec(self.get_cli("recover_meta", groupid))
            assert stat == 0, "Expect recover success"

        finally:
            check_cluster_health()
            # 目录文件删除
            delstat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            assert delstat == 0, "Expect del quota success."
            self.sshclient.ssh_exec("mkdir -p /autotest_rsync")
            rmstat, _ = self.sshclient.ssh_exec("rsync -apgolr --delete /autotest_rsync/ %s/" % self.testpath)
            assert rmstat == 0, "remove dir failed."

    def test_1000w_dir(self):
        """
        3738 单目录下创建1000w 长度255的无规律的子目录(删除、)
        """
        # 3743 对单目录下1000w子目录进行并发删除操作
        script = "for i in {1..10000};do\n" \
                 "  for j in {1..20};do\n" \
                 "    {" \
                 "    for n in {1..50};do\n" \
                 "      mkdir %s/`tr -dc \"0-9,a-z,A-Z\" < /dev/urandom | head -c 255`;done\n" % self.testpath + \
                 "    }&\n"\
                 "done;wait;done\n"
        self.sshclient.ssh_exec("echo '%s' > /tmp/autotest_1000w.sh" % script)
        #脚本执行测试
        self.sshclient.ssh_exec("sh /tmp/autotest_1000w.sh &")
        while True:
            stat, _ = self.sshclient.ssh_exec("ps axu|grep -v grep|grep autotest_1000w.sh > /dev/null 2>&1")
            if stat == 0:
                logger.info("/tmp/autotest_1000w.sh test running.")
                sleep(30)
                continue
            else:
                logger.info("/tmp/autotest_1000w.sh test over.")
                break
        #检验文件数量是否正确
        try:
            _, filenum = self.sshserver.ssh_exec("find %s/* -type d |wc -l" % self.testpath)
            assert filenum == "10000000"
        finally:
            #目录文件删除
            self.sshclient.ssh_exec("mkdir -p /autotest_rsync")
            rmstat, _ = self.sshclient.ssh_exec("rsync -apgolr --delete /autotest_rsync/ %s/" % self.testpath)
            assert rmstat == 0, "remove dir failed."

    def test_disorder_name(self):
        """
        3737 单目录下创建1000w文件长度255的文件名无规律的文件（并发读写、删除）
        """
        #3740 对单目录下1000w文件进行并发读操作
        #3741 对单目录下1000w文件进行并发写操作
        #3742 对单目录下1000w文件进行并发删除操作
        script = "for i in {1..10000};do\n" \
                 "  for j in {1..20};do\n" \
                 "    {" \
                 "    for n in {1..50};do\n" \
                 "      touch %s/`tr -dc \"0-9,a-z,A-Z\" < /dev/urandom | head -c 255`;done\n" % self.testpath + \
                 "    }&\n"\
                 "done;wait;done\n"
        self.sshclient.ssh_exec("echo '%s' > /tmp/autotest_1000w.sh" % script)
        try:
            #脚本执行测试
            self.sshclient.ssh_exec("sh /tmp/autotest_1000w.sh &")
            while True:
                stat, _ = self.sshclient.ssh_exec("ps axu|grep -v grep|grep autotest_1000w.sh > /dev/null 2>&1")
                if stat == 0:
                    logger.info("/tmp/autotest_1000w.sh test running.")
                    sleep(30)
                    continue
                else:
                    logger.info("/tmp/autotest_1000w.sh test over.")
                    break
            #检验文件超过数量限制创建失败
            stat, _ = self.sshclient.ssh_exec("touch %s/`tr -dc \"0-9,a-z,A-Z\" < /dev/urandom|head -c 255`" % self.testpath)
            assert stat != 0, "Expect: more than 1000w touch failed."
            #并发读操作
            stat, _ = self.sshserver.ssh_exec("ls -f %s/*|head -n 100000|xargs -n 100 -P 100|wc -l" % self.testpath)
            assert stat == 0, "Expect: ls success"
            #并发写操作
            stat, _ = self.sshserver.ssh_exec("ls -f %s/*|head -n 100000|xargs -n 100 -P 100 -I {{}} echo 'autotest' > {{}}" % self.testpath)
            assert stat == 0, "Expect: echo success."

        finally:
            #目录文件删除
            self.sshclient.ssh_exec("mkdir -p /autotest_rsync")
            rmstat, _ = self.sshclient.ssh_exec("rsync -apgolr --delete /autotest_rsync/ %s/" % self.testpath)
            assert rmstat == 0, "remove dir failed."