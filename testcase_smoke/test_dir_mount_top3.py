#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import pytest
import random
from time import sleep
from common.util import sshClient
from common.cli import YrfsCli
from config import consts
from depend.client import client_mount

def generate_ip():
    ip = ""
    for n in range(4):
        num = random.randint(0, 255)
        p = ""
        if n > 0:
            p = "."
        ip = ip + p + str(num)
    return ip

yrfs_version = consts.YRFS_VERSION

@pytest.mark.smokeTest
class Test_dirMount(YrfsCli):
    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        self.add_acl = self.get_cli(self, "acl_ip_add")
        self.del_acl = self.get_cli(self, "acl_ip_del")
        self.list_acl = self.get_cli(self, "acl_list")
        self.testdir = "autotest_dirmount_smoke"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)

    def teardown_class(self):
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def setup(self):
        #创建测试目录
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)
        self.sshserver.ssh_exec("yrcli --acl --op=delete --path=/" + self.testdir)
    def teardown(self):
        sleep(1)
        self.sshserver.ssh_exec("yrcli --acl --op=delete --path=/" + self.testdir)
        self.sshserver.ssh_exec("rm -fr " + self.testpath)

    def test_acl_ro(self):
        """
        2000 存储端新增导出目录，权限只读
        """
        try:
            #添加只读权限
            stat ,_ = self.sshserver.ssh_exec(self.add_acl.format(self.testdir, "*", "ro"))
            assert stat == 0, "add acl failed."
            #客户端挂载
            mountstat = client_mount(self.clientip, self.testdir)
            assert mountstat == 0,"client mount failed."
            #写入数据验证
            stat, _ = self.sshclient.ssh_exec("touch %s/fiel1" % consts.MOUNT_DIR)
            assert stat != 0, "ro test failed."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(self.testdir, "*"))

    @pytest.mark.parametrize("ip_end", ("[10-30]","[10-30,35,40]","[1,2,3,8]","*"))
    def test_add_cidr(self, ip_end):
        """
        2004 存储端新增导出目录，ip不限制
        2003 存储端新增导出目录，ip为多个独立IP段
        2002 存储端新增导出目录，ip为模糊区间
        2001 存储端新增导出目录，ip为ip地址段
        """
        ip = generate_ip()
        ip = ip.split(".")[0:3]
        ip_prefix = ".".join(ip) + "."
        ip_cidr = ip_prefix + ip_end
        try:
            #添加acl ip addr
            stat, _ = self.sshserver.ssh_exec(self.add_acl.format(self.testdir, ip_cidr, "rw"))
            assert stat == 0, "add acl failed."
            #查询list状态正常
            self.sshserver.ssh_exec(self.list_acl)
            stat, _ = self.sshserver.ssh_exec(self.list_acl + "|grep -E \"%s|%s\"" % (self.testdir, ip_prefix))
            assert stat == 0, "list acl failed."
        finally:
            stat, _ = self.sshserver.ssh_exec(self.del_acl.format(self.testdir, ip_cidr))
            assert stat == 0, "Delete acl failed."

    def test_not_sign_ip(self):
        """
        2005 存储端新增导出目录，不指定ip
        """
        stat , _ = self.sshserver.ssh_exec("yrcli --acl --op=add --path=%s --mode=rw" % self.testdir)
        assert stat != 0,"add acl success."
        stat, _ = self.sshserver.ssh_exec(self.list_acl + "|grep " + self.testdir)
        assert stat != 0, "list dir success"

    def test_not_sign_path(self):
        """
        2007 存储端新增导出目录，不指定path
        """
        ip = generate_ip()
        stat, _ = self.sshserver.ssh_exec("yrcli --acl --op=add --ip=%s --mode=rw" % ip)
        assert stat != 0, "add acl success."
        stat, _ = self.sshserver.ssh_exec(self.list_acl + "|grep %s" % ip)
        assert stat != 0, "list dir success"

    def test_no_path_list(self):
        """
        2009 存储端支持指定目录路径查询导出目录信息
        """
        ip = generate_ip()
        try:
            self.sshserver.ssh_exec(self.add_acl.format(self.testdir, ip, "rw"))
            _, res = self.sshserver.ssh_exec(self.list_acl + " --path=/autotest_smoke_2009")
            assert not res, "List all dir"
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(self.testdir, ip))

    def test_no_ip_list(self):
        """
        2010 存储端支持不指定IP地址查询导出目录信息
        """
        ip = generate_ip()
        try:
            self.sshserver.ssh_exec(self.add_acl.format(self.testdir, ip, "rw"))
            stat, res = self.sshserver.ssh_exec(self.list_acl + " --ip=17.16.1.250")
            if int(yrfs_version) >= 664:
                assert stat != 0, "list cliacl success."
            else:
                assert stat == 0, "list cliacl failed."
        finally:
            self.sshserver.ssh_exec(self.del_acl.format(self.testdir, ip))

    def test_ip_not_exist(self):
        """
        2012 存储端查询ip地址不存在的导出目录信息
        2013 存储端删除导出目录，不指定ip地址
        2015 存储端删除导出目录，不指定目录
        """
        ip = generate_ip()
        try:
            self.sshserver.ssh_exec(self.add_acl.format(self.testdir, ip, "rw"))
            stat, res = self.sshserver.ssh_exec(self.list_acl + " --path=/%s --ip=%s" % (self.testdir, "192.167.34.123"))
            if int(yrfs_version) >= 664:
                assert stat != 0, "list cliacl success."
            else:
                assert stat == 0, "list cliacl faield."
        finally:
            stat, _ = self.sshserver.ssh_exec("yrcli --acl --op=delete")
            assert stat != 0,"delte acl success"
            stat, _ = self.sshserver.ssh_exec(self.list_acl + "|grep " + self.testdir)
            assert stat == 0, "list dir failed."
            stat , _ = self.sshserver.ssh_exec("yrcli --acl --op=delete --path=/" + self.testdir)
            assert stat == 0, "del acl failed"
        stat, _ = self.sshserver.ssh_exec(self.list_acl + "|grep " + self.testdir)
        assert stat != 0, "list dir success."

