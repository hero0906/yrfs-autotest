# coding=utf-8

'''
@Description  : fsck test
@Time    : 2020/10/21 14:40
@Author  : mayunle
'''
import pytest
import os
import logging
from common.cli import YrfsCli
from common.cluster import getMetaMaster, get_client_storageip
from common.util import sshClient, sshSftp, ping_test
from config import consts
from depend.client import client_mount


logger = logging.getLogger(__name__)

@pytest.mark.serviceTest
class Test_fsck(YrfsCli):

    def setup_class(self):

        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        #获取meta master节点信息
        self.masterips = getMetaMaster()
        for _masterip in self.masterips:
            _ping_stat = ping_test(_masterip)
            if not _ping_stat:
                logger.error("meta master ip address %s unreachable, test skip!" % _masterip)
                pytest.skip(msg="skip, meta master ip address unreachable.", allow_module_level=True)

        sshclient = sshClient(self.clientip)
        sshserver = sshClient(self.serverip)
        sftpclient = sshSftp(self.clientip)

        # IPDIC = get_Cluster_Hostip()
        self.client_storageip = get_client_storageip(self.clientip)

        self.acl_add_cmd = self.get_cli(self, 'acl_ip_add', "", self.client_storageip, "rw")
        self.acl_del_cmd = self.get_cli(self, 'acl_ip_del', "", self.client_storageip)

        mds_map_cmd = self.get_cli(self, "mds_map") + " |awk 'NR>1'|wc -l"
        _, _res_mds = sshserver.ssh_exec(mds_map_cmd)

        #获取fsck command,单mds和双mds
        self.fsck_cmd = []

        if int(_res_mds) > 4:
            self.fsck_cmd.append(self.get_cli(self, "fsck_meta", 0) + "|tail -n 5")
            self.fsck_cmd.append(self.get_cli(self, "fsck_meta", 1) + "|tail -n 5")
            logger.info("multi meta services, meta count: %s." % _res_mds)
        else:
            self.fsck_cmd.append(self.get_cli(self, "fsck_meta", 0) + "|tail -n 5")
            logger.info("single meta services, meta count: %s." % _res_mds)

        logger.info("meta fsck command: %s." % self.fsck_cmd)

        sshserver.ssh_exec(self.acl_add_cmd)

        _mount_stat = client_mount(self.clientip)
        if _mount_stat != 0:
                sshserver.ssh_exec(self.acl_del_cmd)
                logger.error("client mount faild meta fsck case will skip")
                pytest.skip(msg="skip, client mount failed", allow_module_level=True)
        sshserver.close_connect()
    def teardown_class(self):
        sshserver = sshClient(self.serverip)
        sshserver.ssh_exec(self.acl_del_cmd)
        sshserver.close_connect()

    def setup(self):
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        self.sftpclient = sshSftp(self.clientip)
    def teardown(self):
        self.sshclient.close_connect()
        self.sshserver.close_connect()
        self.sftpclient.close_connect()

    def test_fsck_metamaster(self):
        '''
        case1703: fsck工具在meta主节点上启动扫描
        '''
        str_res = []
        for hostip in self.masterips:
            ssh = sshClient(hostip)
            for cmd in self.fsck_cmd:
                logger.info("host %s, %s runing." % (hostip, cmd))
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
                logger.info("fsck result: %s" % tailline)
            ssh.close_connect()

        assert "error" not in "".join(str_res)

    def test_fsck_mixopt(self):
        '''
        case1697: 文件复杂基本操作后，fsck验证主从数据一致性
        '''
        testDir = os.path.join(consts.MOUNT_DIR, 'autotest_fsck_testdir1697')
        self.sftpclient.sftp_mkdir(testDir)

        files = 0
        while files < 100:
            filepath = testDir + "/autotest_fsckfile" + str(files)
            self.sftpclient.sftp_createfile(filepath)
            self.sftpclient.sftp_truncate(filepath,10)
            self.sftpclient.sftp_rename(filepath,filepath + "rename")
            files += 1
        delfiles = 0
        while delfiles < 20:
            delfilepath = testDir + "/autotest_fsckfile" + str(delfiles) + "rename"
            self.sftpclient.sftp_remove(delfilepath)
            delfiles += 1

        str_res = []
        #IPDIC = get_Cluster_Hostip()
        for hostip in self.masterips:
            ssh = sshClient(hostip)
            for cmd in self.fsck_cmd:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()

        self.sshserver.ssh_exec("rm -fr %s" % testDir)
        #self.sftpclient.sftp_rmdir(testDir)
        assert "error" not in "".join(str_res)

    def test_fsck_cp(self):
        '''
        case1696,cp文件后，fsck验证主从数据一致性
        '''
        #testDir = "/mnt/yrfs/autotest_fsck_testdir1696"
        testDir = os.path.join(consts.MOUNT_DIR, 'autotest_fsck_testdir1696')
        dir1Path = testDir + "/autotest_dir1"
        dir2Path = testDir + "/autotest_dir2"

        self.sftpclient.sftp_mkdir(testDir, 777)
        self.sftpclient.sftp_mkdir(dir1Path,777)
        self.sftpclient.sftp_mkdir(dir2Path,777)

        files = 0
        while files < 100:
            filepath = dir1Path + "/autotest_fsckfile" + str(files)
            self.sftpclient.sftp_createfile(filepath)
            cmd = "cp " + filepath + "  " +dir2Path +"/autotest_fsckrename" + str(files)
            self.sshclient.ssh_exec(cmd)
            #shutil.copy(filepath,dir2Path + "/fsckrename" + str(files))
            files += 1

        str_res = []
        #IPDIC = get_Cluster_Hostip()
        for hostip in self.masterips:
            ssh = sshClient(hostip)
            #hostip = self.IPDIC[host]
            for cmd in self.fsck_cmd:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()

        self.sshserver.ssh_exec("rm -fr %s" % testDir)

        assert "error" not in "".join(str_res)

    def test_fsck_mv(self):
        '''
        case1695,跨目录mv文件后，fsck验证主从数据一致性
        '''
        testDir = os.path.join(consts.MOUNT_DIR, 'autotest_fsck_testdir1695')
        dir1Path = testDir+"/autotest_dir1"
        dir2Path = testDir+"/autotest_dir2"

        self.sftpclient.sftp_mkdir(testDir)
        self.sftpclient.sftp_mkdir(dir1Path)
        self.sftpclient.sftp_mkdir(dir2Path)

        files = 0
        while files < 100:
            filepath = dir1Path + "/autotest_fsckfile" + str(files)
            self.sftpclient.sftp_createfile(filepath)
            self.sftpclient.sftp_rename(filepath,dir2Path + "/autotest_fsckmv" + str(files))
            #shutil.move(filepath,dir2Path + "/fsckmv" + str(files))
            files += 1
        str_res = []
        #IPDIC = get_Cluster_Hostip()
        for hostip in self.masterips:
            ssh = sshClient(hostip)
            #hostip = self.IPDIC[host]
            for cmd in self.fsck_cmd:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()
            #str_res = str_res + tailline
        self.sshserver.ssh_exec("rm -fr %s" % testDir)

        assert "error" not in "".join(str_res)

    def test_fsck_rename(self):
        '''
        case1694,重命名文件后，fsck验证主从数据一致性
        '''
        #testDir = "/mnt/yrfs/autotest_fsck_testdir1694"
        testDir = os.path.join(consts.MOUNT_DIR, 'autotest_fsck_testdir1694')
        self.sftpclient.sftp_mkdir(testDir)

        files = 0
        while files < 100:
            filepath = testDir + "/autotest_fsckfile" + str(files)
            self.sftpclient.sftp_createfile(filepath)
            self.sftpclient.sftp_rename(filepath, filepath + "rename")
            files += 1

        str_res = []
        #IPDIC = get_Cluster_Hostip()
        for hostip in self.masterips:
            #hostip = self.IPDIC[host]
            ssh = sshClient(hostip)
            for cmd in self.fsck_cmd:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()
        #6、清理测试数据，删除创建的测试文件
        #7、验证测试结果
        self.sshserver.ssh_exec("rm -fr %s" % testDir)

        assert "error" not in "".join(str_res)

    def test_fsck_truncate(self):
        '''
        case1693,截断文件后，fsck验证主从数据一致性
        '''
        #testDir = "/mnt/yrfs/autotest_fsck_testdir1693"
        testDir = os.path.join(consts.MOUNT_DIR, 'autotest_fsck_testdir1693')
        self.sftpclient.sftp_mkdir(testDir)

        files = 0
        while files < 100:
            filepath = testDir + "/autotest_fsckfile" + str(files)
            self.sftpclient.sftp_createfile(filepath,'w')
            self.sftpclient.sftp_truncate(filepath,10)
            files += 1

        str_res = []
        # IPDIC = get_Cluster_Hostip()
        for hostip in self.masterips:
            ssh = sshClient(hostip)
            #hostip = self.IPDIC[host]
            for cmd in self.fsck_cmd:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()

        self.sshserver.ssh_exec("rm -fr %s" % testDir)

        assert "error" not in "".join(str_res)