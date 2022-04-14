#!/usr/bin/env python
# -*- coding:utf-8 -*-

from uuid import uuid4
import pytest
from time import sleep
from common.util import sshClient
from config import consts
from depend.nfsdepend import NfsRest


@pytest.mark.skip(msg="not finish")
class Test_nfsShare():

    def setup_class(self):
        # 获取nfs域名
        self.nfsrest = NfsRest()
        self.nfs_domain = self.nfsrest.get_dns_name()
        if not self.nfs_domain:
            pytest.skip(msg="not found nfs domain", allow_module_level=True)
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        #创建普通用户并设置密码
        self.normal_user = "autotest"
        userstat, _ = self.sshclient.ssh_exec("cat /etc/passwd|grep " + self.normal_user)
        if userstat != 0:
            self.sshclient.ssh_exec("useradd {0}&&echo {0}:{1}|chpasswd".format(self.normal_user, consts.PASSWORD))
        #创建测试目录
        self.testdir = "autotest_nfs_share_" + str(uuid4())[:5]
        self.mountdir = consts.MOUNT_DIR
        # 创建共享目录
        self.sshserver.ssh_exec("cd %s&&mkdir %s" % (self.mountdir, self.testdir))
        # 创建nfs share
        self.target_id, self.share_id = self.nfsrest.add_share(self.testdir)
        #挂载共享目录
        #self.sshclient.ssh_exec("mount -t nfs {0}:{1}/{2} {1}".format(self.nfs_domain, self.mountdir, self.testdir))
        #普通用户登录
        #self.sshuser = sshClient(self.clientip, username=self.normal_user)

    def teardown_class(self):
        #清除共享和目录
        self.nfsrest.del_share(self.target_id, self.share_id )
        self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
        self.sshclient.ssh_exec("umount -l " + self.mountdir)
        self.sshclient.close_connect()
        self.sshserver.close_connect()
        #self.sshuser.close_connect()

    @pytest.mark.parametrize("root_permiss", ("root_squash", "no_root_squash"))
    @pytest.mark.parametrize("permiss", ("all_squash", "no_all_squash"))
    @pytest.mark.parametrize("write_mode", ("sync", "async"))
    @pytest.mark.parametrize("mode", ("rw", "ro"))
    @pytest.mark.parametrize("user", ("root", "autotest"))
    def test_nfs_share(self, root_permiss, permiss, write_mode, mode, user):
        """
        nfs 权限控制测试
        """
        sleep(1)
        try:
            stat = self.nfsrest.update_share(self.target_id,root_permiss,permiss,write_mode,mode)
            assert stat, "Expect update nfs acl sucsess"
            # #客户端执行挂载nfs服务
            # stat, _ = self.sshclient.ssh_exec("mount -t nfs {0}:{1}/{2} {1}".format(self.nfs_domain, self.mountdir, self.testdir))
            # assert stat == 0, "Expect mount failed."
        finally:
            pass
            #self.sshclient.ssh_exec("umount -l " + self.mountdir)

