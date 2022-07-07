#coding=utf-8
'''
@Desciption : s3 tiering test case.
@Time : 2021/1/18 18:58
@Author : caoyi
'''

import pytest
import os
import re
from time import sleep
import logging
from config import consts
from common.util import sshClient
from common.cli import YrfsCli
from common.cluster import fsck

logger = logging.getLogger(__name__)

yrfs_version = consts.YRFS_VERSION[:2]

@pytest.mark.skipif(yrfs_version != "65",reason="only 65* verison need run.")
class TesttieringFunc(YrfsCli):
    '''
    分层测试用例集合
    '''
    serverip = consts.CLUSTER_VIP
    clientip = consts.CLIENT[0]

    def setup_class(self):

        try:
            sshserver = sshClient(self.serverip)
            _, check_s3_res = sshserver.ssh_exec(self.get_cli(self,"get_s3_config"))
            if "HTTP" not in check_s3_res:
                pytest.skip(msg="skip, s3 config not found.", allow_module_level=True)

            rm_stat, _ = sshserver.ssh_exec("rm -fr %s/*" % consts.MOUNT_DIR)
            fio_stat, _ = sshserver.ssh_exec("fio --version")
            if rm_stat != 0 and fio_stat != 0:
                pytest.skip(msg="skip, cann't clean / files or fio not found.", allow_module_level=True)
        finally:
            sshserver.close_connect()

    def teardown_class(self):
        pass

    def test_s3_delfile(self):
        '''
        caseID: 2481 校验删除过程中，读写其他目录文件正常
        '''
        try:
            sshserver = sshClient(self.serverip)
        # 测试目录、文件创建
            testdir1 = "autotest/dir1"
            testdir2 = "autotest/dir2"
            testdir3 = "autotest/dir3"

            testpath1 = os.path.join(consts.MOUNT_DIR, testdir1)
            testpath2 = os.path.join(consts.MOUNT_DIR, testdir2)
            testpath3 = os.path.join(consts.MOUNT_DIR, testdir3)

            fio = "fio -iodepth=16 -numjobs=1 -size=100M -bs=4K -time_based -runtime=6000 -ioengine=psync " + \
                  "-rw=write -name=test -filename=%s/autotest_file &" % testpath3
            # 目录创建
            sshserver.ssh_exec("mkdir -p " + testpath1)
            sshserver.ssh_exec("mkdir -p " + testpath2)
            sshserver.ssh_exec("mkdir -p " + testpath3)

            #pid = os.fork()
            #if pid == 0:
            #后台运行fio业务
            sshserver.ssh_exec(fio)
            sleep(1)
            for num in range(1,21):
                sshserver.ssh_exec("dd if=/dev/zero of=%s/dd%s bs=4K count=2" % (testpath1, str(num)))
                sshserver.ssh_exec("dd if=/dev/zero of=%s/dd%s bs=1M count=10" % (testpath2, str(num)))
            #校验文件md5sum
            _, file_md5 = sshserver.ssh_exec("md5sum " + testpath2 + "/dd1")
            #执行上传动作
            set_tier_stat, _ = sshserver.ssh_exec(self.get_cli("set_tier_time","60"))
            assert set_tier_stat == 0, "set tiering timeoff failed."
            sleep(60)
            exec_stat, _ = sshserver.ssh_exec(self.get_cli("s3_imexec"))
            assert exec_stat == 0, "executeRequestScheduleTime execute failed."
            sleep(60)
            #查看文件是否已上传成功
            for num in range(1,21):
                for i in range(20):
                    _, layer_res = sshserver.ssh_exec(self.get_cli("get_entry",testdir1 + "/dd" + str(num)))
                    layer = re.findall("Layer: (.*)", layer_res)
                    layer = "".join(layer)
                    if layer == "S3":
                        logger.info("file %s in S3 layer." % (testdir1 + "/dd" + str(num)))
                        break
                    else:
                        logger.error("file %s not in S3 layer. retry again after 5s." % (testdir1 + "/dd" + str(num)))
                        sleep(5)
                assert layer == "S3", "s3 upload failed."

            for num in range(1, 21):
                for i in range(20):
                    _, layer_res = sshserver.ssh_exec(self.get_cli("get_entry", testdir2 + "/dd" + str(num)))
                    layer = re.findall("Layer: (.*)", layer_res)
                    layer = "".join(layer)
                    if layer == "S3":
                        logger.info("file %s in S3 layer." % (testdir2 + "/dd" + str(num)))
                        break
                    else:
                        logger.error("file %s not in S3 layer. retry again after 5s." % (testdir2 + "/dd" + str(num)))
                        sleep(5)
                assert layer == "S3", "s3 upload failed."

            #删除部分上传文件
            rm_stat, _ = sshserver.ssh_exec("rm -fr " + testpath1)
            assert rm_stat == 0, "rm dir failed."
            #检测文件的fsck
            fsck_stat = fsck()
            assert fsck_stat == 0, "fsck failed."
            #再次校验文件的md5值
            _, file_md5_2 = sshserver.ssh_exec("md5sum  " + testpath2 + "/dd1")
            assert file_md5 == file_md5_2, "md5sum verify error."
            #检测fio业务是否还在运行中
            fio_stat, _ = sshserver.ssh_exec("ps axu|grep fio|grep -v grep")
            assert fio_stat == 0, "fio not runing."

        finally:
            sshserver.ssh_exec("ps axu|grep fio|grep -v grep|awk '{print $2}'|xargs kill -9")
            rm_stat, _ = sshserver.ssh_exec("rm -fr %s" % os.path.join(consts.MOUNT_DIR, "autotest"))
            sshserver.close_connect()
            assert rm_stat == 0, "rm dir failed."

    def test_batch_smallfile(self):
        '''
        2445 校验并发下载海量小文件是否有效
        '''
        testdir = "autotest/"
        testpath = consts.MOUNT_DIR + "/" + testdir
        files = 1001

        try:
            sshserver = sshClient(self.serverip)
            sshserver.ssh_exec("mkdir -p " + testpath)
            for num in range(1,files):
                sshserver.ssh_exec("dd if=/dev/zero of=%s%s bs=1K count=1" % (testpath,str(num)))

            #上传操作
            set_tier_stat, _ = sshserver.ssh_exec(self.get_cli("set_tier_time", "60"))
            assert set_tier_stat == 0, "set tiering timeoff failed."
            sleep(60)
            exec_stat, _ = sshserver.ssh_exec(self.get_cli("s3_imexec"))
            assert exec_stat == 0, "executeRequestScheduleTime execute failed."
            #检测上传是否成功
            sleep(60)
            for num in range(1,files):
                for i in range(30):
                    _, layer_res = sshserver.ssh_exec(self.get_cli("get_entry", testdir + str(num)))
                    layer = re.findall("Layer: (.*)", layer_res)
                    layer = "".join(layer)
                    if layer == "S3":
                        logger.info("file %s in S3 layer." % (testdir + str(num)))
                        break
                    else:
                        logger.error("file %s not in S3 layer. retry again after 5s." % (testdir + str(num)))
                        sleep(5)
                assert layer == "S3", "s3 upload failed."
            #下载文件
            for num in range(1,files):
                md5_stat, _ = sshserver.ssh_exec("md5sum " + testpath + str(num))
            sleep(120)
            #检查文件是否下载成功
            for num in range(1,files):
                for i in range(30):
                    _, layer_res = sshserver.ssh_exec(self.get_cli("get_entry", testdir + str(num)))
                    layer = re.findall("Layer: (.*)", layer_res)
                    layer = "".join(layer)
                    if layer == "Local":
                        logger.info("file %s in local layer." % (testdir + str(num)))
                        break
                    else:
                        logger.error("file %s not in local layer. retry again after 5s." % (testdir + str(num)))
                        sleep(5)
                assert layer == "Local", "download file failed."
            #数据fsck一致性校验
            fsck_stat = fsck()
            assert fsck_stat == 0, "fsck verify failed."
        finally:
            rm_stat, _= sshserver.ssh_exec("rm -fr " + testpath)
            sshserver.close_connect()
            assert rm_stat == 0, "rm dir failed."

    def test_multilayer_dir(self):
        '''
        caseID: 2440 校验在多层目录上传过程中，读写删非上传目录文件有效
        '''
        testdir1 = "autotest/dir1/dir2/dir3/dir4/dir5/dir6/dir7/"
        testdir2 = "autotest/dir2/dir3/dir4/dir5/"
        testdir3 = "autotest/dir4/dir5/dir6/dir7/dir8/"
        testpath1 = os.path.join(consts.MOUNT_DIR, testdir1)
        testpath2 = os.path.join(consts.MOUNT_DIR, testdir2)
        testpath3 = os.path.join(consts.MOUNT_DIR, testdir3)

        try:
            sshserver = sshClient(self.serverip)

            #创建测试数据
            sshserver.ssh_exec("mkdir -p " + testpath1)
            sshserver.ssh_exec("mkdir -p " + testpath2)
            sshserver.ssh_exec("mkdir -p " + testpath3)
            for num in range(1,21):
                sshserver.ssh_exec("dd if=/dev/zero of=%s%s bs=4K count=1" % (testpath1, str(num)))
                sshserver.ssh_exec("dd if=/dev/zero of=%s%s bs=200K count=1" % (testpath2, str(num)))

            #设置s3上传规则
            set_tier_stat, _ = sshserver.ssh_exec(self.get_cli("set_tier_time", "60"))
            assert set_tier_stat == 0, "set tiering timeoff failed."
            sleep(60)
            exec_stat, _ = sshserver.ssh_exec(self.get_cli("s3_imexec"))
            assert exec_stat == 0, "executeRequestScheduleTime execute failed."
            #读写操作其他数据
            for num in range(1,11):
                sshserver.ssh_exec("dd if=/dev/zero of=%s%s bs=4M count=1" % (testpath3, str(num)))
            for num in range(1,11):
                md5_stat, _ = sshserver.ssh_exec("md5sum " + testpath3 + str(num))
                assert md5_stat == 0, "md5sum operation failed."
            for num in range(1,11):
                rm_stat, _ = sshserver.ssh_exec("rm -fr " + testpath3 + str(num))
                assert rm_stat == 0, "remove file failed."
        finally:
            rm_stat, _ = sshserver.ssh_exec("rm -fr " + os.path.join(consts.MOUNT_DIR,"autotest"))
            sshserver.close_connect()
            assert rm_stat == 0, "rm dir failed."

    def test_section(self):
        '''
        caseID: 2439 校验大文件，切片情况
        '''
        testdir = "autotest/"
        testpath = os.path.join(consts.MOUNT_DIR, testdir)

        try:
            sshserver = sshClient(self.serverip)
            sshserver.ssh_exec("mkdir -p " + testpath)
            #查看集群的group数量
            _, oss_groups = sshserver.ssh_exec(self.get_cli("group_list","oss") + "|awk 'NR>1'|wc -l")
            #创建与group组数量同等的文件
            sshserver.ssh_exec(self.get_cli("create_file","1M",oss_groups,testdir + "testfile","mirror"))
            #创建测试文件
            sshserver.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024" % (testpath + "testfile"))
            md5sum1, _ = sshserver.ssh_exec("md5sum " + testpath + "testfile")
            #文件上传操作
            set_tier_stat, _ = sshserver.ssh_exec(self.get_cli("set_tier_time", "60"))
            assert set_tier_stat == 0, "set tiering timeoff failed."
            sleep(60)
            exec_stat, _ = sshserver.ssh_exec(self.get_cli("s3_imexec"))
            assert exec_stat == 0, "executeRequestScheduleTime execute failed."
            #校验上传状态
            for i in range(100):
                _, layer_res = sshserver.ssh_exec(self.get_cli("get_entry", testdir + "testfile"))
                layer = re.findall("Layer: (.*)", layer_res)
                layer = "".join(layer)
                if layer == "S3":
                    logger.info("file %s in S3 layer." % (testdir + "testfile"))
                    break
                else:
                    logger.error("file %s not in S3 layer. retry again after 5s." % (testdir + "testfile"))
                    sleep(5)
            assert layer == "S3", "upload file failed."
            #查看切片状态
            _, s3_res = sshserver.ssh_exec(self.get_cli("get_s3") + "|awk 'NR>2'")
            for line in s3_res.split("\n"):
                assert line.split()[2] == "0B", "s3 data inequality."

            #再次校验文件md5sum
            _, md5sum2 = sshserver.ssh_exec("md5sum " + testpath + "testfile")
            assert md5sum1 == md5sum2, "file md5sum error."
        finally:
            rm_stat, _ = sshserver.ssh_exec("rm -fr " + testpath)
            sshserver.close_connect()
            assert rm_stat == 0, "rm file failed."
