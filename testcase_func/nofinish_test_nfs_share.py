#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pytest
import time
import os
from time import sleep
from common.util import sshClient
from config import consts
from depend.nfsdepend import NfsRest


#@pytest.mark.skip(msg="not finish")
class Test_nfsShare():

    def setup_class(self):
        # 获取nfs域名，获取失败不执行
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
        userstat, _ = self.sshclient.ssh_exec("cat /etc/passwd|grep -w " + self.normal_user)
        if userstat != 0:
            self.sshclient.ssh_exec("useradd {0}&&echo {0}:{1}|chpasswd".format(self.normal_user, consts.PASSWORD))
        userstat, _ = self.sshserver.ssh_exec("cat /etc/passwd|grep -w " + self.normal_user)
        if userstat != 0:
            self.sshserver.ssh_exec("useradd {0}&&echo {0}:{1}|chpasswd".format(self.normal_user, consts.PASSWORD))
        #创建测试目录
        self.testdir = "autotest_nfs_" + time.strftime("%m-%d-%H%M%S")
        self.mountdir = consts.MOUNT_DIR
        self.testpath = os.path.join(self.mountdir, self.testdir)
        # 创建共享目录
        self.nobody_testfile = "autotest_nobody"
        self.other_testfile = "autotest_other"
        self.root_testfile = "autotest_root"
        self.sshserver.ssh_exec("cd %s&&mkdir %s" % (self.mountdir, self.testdir))
        # 创建测试文件
        self.sshserver.ssh_exec("cd {0}&&touch {1}&&chown nfsnobody:nfsnobody {1}".format(self.testpath,
                                                                                            self.nobody_testfile))
        self.sshserver.ssh_exec("cd {0}&&touch {1}&&chown {2}:{2} {1}".format(self.testpath,
                                                                        self.other_testfile, self.normal_user))
        self.sshserver.ssh_exec("cd {0}&&touch {1}".format(self.testpath, self.root_testfile))
        # 创建nfs share
        sleep(5)
        self.target_id, self.share_id = self.nfsrest.add_share(self.testdir)
        #普通用户登录
        self.sshuser = sshClient(self.clientip, username=self.normal_user)
        #配置dns 解析
        dns_ips = self.nfsrest.get_dns_ip()
        for ip in dns_ips:
            stat, _  = self.sshclient.ssh_exec("cat /etc/resolv.conf|grep " + ip)
            if stat != 0:
                self.sshserver.ssh_exec("sed -i '1 i %s' /etc/resolv.conf" % ip)
        self.mount_nfs = "mount -t nfs {0}:{1}/{2} {1}".format(self.nfs_domain, self.mountdir, self.testdir)
        # #执行nfs挂载
        sleep(2)
        # self.sshclient.ssh_exec("mkdir -p " + self.mountdir)
        # stat, _ = self.sshclient.ssh_exec(self.mount_nfs)
        # if stat != 0:
        #     pytest.skip(msg="nfs client mount failed.", allow_module_level=True)

    def teardown_class(self):
        #清除共享和目录
        self.nfsrest.del_share(self.target_id, self.share_id)
        self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, self.testdir))
        self.sshclient.ssh_exec("umount " + self.mountdir)
        self.sshclient.close_connect()
        self.sshserver.close_connect()
        self.sshuser.close_connect()

    @pytest.mark.parametrize("permiss", ("all_squash", "no_all_squash"))
    @pytest.mark.parametrize("root_permiss", ("root_squash", "no_root_squash"))
    @pytest.mark.parametrize("write_mode", ("sync", "async"))
    @pytest.mark.parametrize("mode", ("rw", "ro"))
    @pytest.mark.parametrize("user", ("root", "autotest"))
    def test_nfs_share(self, permiss, root_permiss, write_mode, mode, user):
        """
        caseID3487-3510 验证nfs不同权限下配置，实际权限符合预期
        """
        try:
            #配置dns权限
            stat = self.nfsrest.update_share(self.target_id,root_permiss,permiss,write_mode,mode)
            assert stat, "Expect update nfs acl sucsess"
            # 客户端执行挂载nfs服务
            sleep(5)
            #不同用户的权限验证
            if user == "root":
                stat, _ = self.sshclient.ssh_exec(self.mount_nfs)
                assert stat == 0, "Expect:mount success."

                nobody_wstat, _ = self.sshclient.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.nobody_testfile))
                nobody_rstat, _ = self.sshclient.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.nobody_testfile))
                other_wstat, _ = self.sshclient.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.other_testfile))
                other_rstat, _ = self.sshclient.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.other_testfile))
                root_wstat, _ = self.sshclient.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.root_testfile))
                root_rstat, _ = self.sshclient.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.root_testfile))
                #mode 等于ro无写权限
                if mode == "ro":
                    assert nobody_wstat != 0 and other_wstat != 0 and root_wstat != 0, "Expect: write permissions correct."
                    assert nobody_rstat == 0 and other_rstat == 0 and root_rstat == 0, "Expect: read permissions correct."
                #NFS共享目录设置all_squash， root_squash，读写权限，客户端使用root用户挂载并进行读写删除等操作
                if permiss == "all_squash" and mode == "rw" and user == "root":
                    assert nobody_wstat == 0 and other_wstat == 0 and root_wstat != 0, "Expect: write permissions correct."
                    assert nobody_rstat == 0 and other_rstat == 0 and root_rstat == 0, "Expect: read permissions correct."
                #3491 NFS共享目录设置no_all_squash， root_squash，读写权限，客户端使用root用户挂载并进行读写删除等操作
                if permiss == "no_all_squash" and root_permiss == "root_squash" and mode == "rw" and user == "root":
                    assert nobody_wstat == 0 and other_wstat != 0 and root_wstat != 0, "Expect: write permissions correct."
                    assert nobody_rstat == 0 and other_rstat == 0 and root_rstat == 0, "Expect: read permissions correct."
                # 3493 NFS共享目录设置no_all_squash，no_root_squash，读写权限，客户端使用root用户挂载并进行读写删除等操作
                if permiss == "no_all_squash" and root_permiss == "no_root_squash" and mode == "rw" and user == "root":
                    assert nobody_wstat == 0 and other_wstat != 0 and root_wstat != 0, "Expect: write permissions correct."
                    assert nobody_rstat == 0 and other_rstat == 0 and root_rstat == 0, "Expect: read permissions correct."
            else:
                stat, _ = self.sshuser.ssh_exec(self.mount_nfs)
                assert stat == 0, "Expect:mount success."
                nobody_wstat, _ = self.sshuser.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.nobody_testfile))
                nobody_rstat, _ = self.sshuser.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.nobody_testfile))
                other_wstat, _ = self.sshuser.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.other_testfile))
                other_rstat, _ = self.sshuser.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.other_testfile))
                root_wstat, _ = self.sshuser.ssh_exec("cd %s&&echo fsdggf > %s" % (self.mountdir, self.root_testfile))
                root_rstat, _ = self.sshuser.ssh_exec("cd %s&&cat %s" % (self.mountdir, self.root_testfile))
                if permiss == "all_squash" and mode == "rw":
                    assert nobody_wstat == 0 and other_wstat == 0 and root_wstat != 0, "Expect: write permissions correct."
                    assert nobody_rstat == 0 and other_rstat == 0 and root_rstat == 0, "Expect: read permissions correct."

        finally:
            sleep(2)
            self.sshclient.ssh_exec("umount " + self.mountdir)
            #self.sshserver.ssh_exec("umount " + self.mountdir)

