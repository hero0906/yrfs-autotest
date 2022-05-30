# coding=utf-8
'''
@Desciption : test subdir mount
@Time : 2020/02/02 11:13
@Author : caoyi
'''


import pytest
import os
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.client import client_mount
from common.cluster import get_client_storageip


@pytest.mark.funcTest
class Test_subdirMountFunc(YrfsCli):
    '''
    子目录挂载用例合集,需要两个客户端
    '''
    def setup_class(self):
        self.client_amount = len(consts.CLIENT)

        if self.client_amount >= 2:
            self.client2 = consts.CLIENT[1]
            self.sshclient2 = sshClient(self.client2)
            self.client2_stor_ip = get_client_storageip(self.client2)
            #pytest.skip(msg="skip, need two client", allow_module_level=True)

        self.client1 = consts.CLIENT[0]
        self.server = consts.META1

        self.client1_stor_ip = get_client_storageip(self.client1)

        self.testdir = "autotest_dirmount"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)

        self.sshclient1 = sshClient(self.client1)
        self.sshserver = sshClient(self.server)

    def setup(self):
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)

    def teardown(self):
        self.sshserver.ssh_exec("rm -fr " + self.testpath)

    def teardown_class(self):
        self.sshserver.close_connect()
        self.sshclient1.close_connect()
        if self.client_amount >= 2:
            self.sshclient2.close_connect()

    def test_subdir_inherit_parentdir_rw(self):
        '''
        caseID2032: 父子目录同时挂载时，父目录设置读写权限，子目录只读权限，子目录权限为读写。
        '''
        try:

            #client1_stor_ip = get_client_storageip(self.client1)

            subdir = self.testdir + "/subdir1"
            subpath = os.path.join(consts.MOUNT_DIR, subdir)
            self.sshserver.ssh_exec("mkdir -p " + subpath)

            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", subdir,self.client1_stor_ip, "ro"))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, self.client1_stor_ip, "rw"))

            client_mount(self.client1, self.testdir)
            stat1, _ = self.sshclient1.ssh_exec("dd if=/dev/zero of=%s/testfile bs=1M count=10" % consts.MOUNT_DIR)
            client_mount(self.client1, subdir)
            stat2, _ = self.sshclient1.ssh_exec("dd if=/dev/zero of=%s/testfile bs=1M count=10" % consts.MOUNT_DIR)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", subdir, self.client1_stor_ip))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, self.client1_stor_ip))

        assert stat1 == 0 and stat2 == 0,"subdir acl inherit parentdir failed"

    def test_subdir_inherit_parentdir_ro(self):
        '''
        caseID:2031 父子目录同时挂载时，父目录设置只读权限，子目录设置读写权限，子目录权限为只读
        '''
        try:
            subdir = self.testdir + "/subdir1"
            subpath = os.path.join(consts.MOUNT_DIR, subdir)
            self.sshserver.ssh_exec("mkdir -p " + subpath)

            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", subdir, self.client1_stor_ip, "rw"))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, self.client1_stor_ip, "ro"))

            client_mount(self.client1, self.testdir)
            stat1, _ = self.sshclient1.ssh_exec("touch %s/testfile1" % consts.MOUNT_DIR)
            client_mount(self.client1, subdir)
            stat2, _ = self.sshclient1.ssh_exec("touch %s/testfile1" % consts.MOUNT_DIR)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", subdir, self.client1_stor_ip))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, self.client1_stor_ip))

        assert stat1 != 0 and stat2 != 0,"subdir acl inherit parentdir failed"

    #@pytest.mark.skipif(self.client_amount < 2,reason="need two client")
    @pytest.mark.skip
    def test_subdir_segment_acl(self):
        '''
        caseID:2022 同一个子目录不同网段多个细粒度权限,挂载权限以最小细粒度为准
        '''
        if self.client_amount < 2:
            pytest.skip(msg="need two client")
        client1_ipprefix = self.client1_stor_ip.split('.')[:3]
        client1_ipend = self.client1_stor_ip.split('.')[-1]
        client2_ipprefix = self.client2_stor_ip.split('.')[:3]
        client2_ipend = self.client2_stor_ip.split('.')[-1]

        try:
            if client1_ipprefix != client2_ipprefix:
                pytest.skip(msg="client not in the same network segment,testcase skip.")
            else:
                if int(client1_ipend) < int(client2_ipend):
                    ip_segment = client2_ipend + "-255"
                else:
                    ip_segment = "1-" + client2_ipend

            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, self.client1_stor_ip, "rw"))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, '.'.join(client2_ipprefix) + ".[%s]", "rw") % ip_segment)
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, '.'.join(client2_ipprefix) + ".*", "ro"))


            client_mount(self.client1, self.testdir)
            client_mount(self.client2, self.testdir)

            dd_stat1, _ = self.sshclient1.ssh_exec("touch %s/testfile1" % consts.MOUNT_DIR)
            dd_stat2, _ = self.sshclient2.ssh_exec("touch %s/testfile2" % consts.MOUNT_DIR)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, self.client1_stor_ip))
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, '.'.join(client2_ipprefix) + ".[%s]") % ip_segment)
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, '.'.join(client2_ipprefix) + ".*"))

        assert dd_stat1 == 0 and dd_stat2 == 0, "touch file failed"

    #@pytest.mark.skipif(client_amount < 2, reason="need two client")
    def test_subdir_twoclient_ro(self):
        '''
        caseID: 2020同一挂载点挂载到不同客户端相同目录，设置只读权限。
        '''
        if self.client_amount < 2:
            pytest.skip(msg="need two client")
        client1_ipprefix = self.client1_stor_ip.split('.')[:3]
        client1_ipend = self.client1_stor_ip.split('.')[-1]
        client2_ipprefix = self.client2_stor_ip.split('.')[:3]
        client2_ipend = self.client2_stor_ip.split('.')[-1]

        try:
            if client1_ipprefix != client2_ipprefix:
                pytest.skip(msg="client not in the same network segment,testcase skip.")
            else:
                if int(client1_ipend) < int(client2_ipend):
                    ip_segment = client1_ipend + "-" + client2_ipend
                else:
                    ip_segment = client2_ipend + "-" + client1_ipend

            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, '.'.join(client2_ipprefix) + ".[%s]", "ro") % ip_segment)

            client_mount(self.client1, self.testdir)
            client_mount(self.client2, self.testdir)

            touch_stat1, _ = self.sshclient1.ssh_exec("touch %s/testfile1" % consts.MOUNT_DIR)
            touch_stat2, _ = self.sshclient2.ssh_exec("touch %s/testfile2" % consts.MOUNT_DIR)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, '.'.join(client2_ipprefix) + ".[%s]") % ip_segment)

        assert touch_stat1 != 0 and touch_stat2 != 0, "touch file success."

    #@pytest.mark.skipif(client_amount < 2, reason="need two client")
    def test_subdir_twoclient_rw(self):
        """
        caseID: 2019 同一个挂载点挂载到不同客户端的相同目录，设置读写权限
        """
        if self.client_amount < 2:
            pytest.skip(msg="need two client")

        client1_ipprefix = self.client1_stor_ip.split('.')[:3]
        client1_ipend = self.client1_stor_ip.split('.')[-1]
        client2_ipprefix = self.client2_stor_ip.split('.')[:3]
        client2_ipend = self.client2_stor_ip.split('.')[-1]

        try:
            if client1_ipprefix != client2_ipprefix:
                pytest.skip(msg="client not in the same network segment,testcase skip.")
            else:
                if int(client1_ipend) < int(client2_ipend):
                    ip_segment = client1_ipend + "-" + client2_ipend
                else:
                    ip_segment = client2_ipend + "-" + client1_ipend

            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, '.'.join(client2_ipprefix) + ".[%s]", "rw") % ip_segment)

            client_mount(self.client1, self.testdir)
            client_mount(self.client2, self.testdir)

            touch_stat1, _ = self.sshclient1.ssh_exec("touch %s/testfile1" % consts.MOUNT_DIR)
            touch_stat2, _ = self.sshclient2.ssh_exec("touch %s/testfile2" % consts.MOUNT_DIR)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, '.'.join(client2_ipprefix) + ".[%s]") % ip_segment)

        assert touch_stat1 == 0 and touch_stat2 == 0, "touch file failed."