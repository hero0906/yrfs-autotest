# coding=utf-8
"""
@Desciption : s3 tiering mirror case suite
@Time : 2020/5/27 18:47
@Author : caoyi
"""

import pytest
import logging
from time import sleep
import time
import os
import re
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from common.client import client_mount
from common.s3depend import check_layer
from common.cluster import fsck, check_cluster_health

logger = logging.getLogger(__name__)

yrfs_version = int(consts.YRFS_VERSION[:2])

#指定s3分层模式
@pytest.fixture(scope="function", params=["1"])
def get_data(request):
    """
    :param request:
    :return:  s3 mode seek or normal
    """
    return request.param


@pytest.mark.skipif(yrfs_version <= 66, reason="only 66* verison need run.")
# @pytest.mark.skip(reason="Expect skip")
@pytest.mark.funcTest
class TesttieringMirror(YrfsCli):

    def setup_class(self):
        # 变量定义
        self.client1 = consts.CLIENT[0]
        self.serverip = consts.CLUSTER_VIP
        self.sshclient1 = sshClient(self.client1)
        self.sshserver = sshClient(self.serverip)
        # 检验客户端fio测试工具是否存在
        fio_stat, _ = self.sshclient1.ssh_exec("fio --version")
        if fio_stat != 0:
            yum_stat, _ = self.sshclient1.ssh_exec("yum -y install fio")
            if yum_stat != 0:
                yum_stat, _ = self.sshclient1.ssh_exec("apt-get install fio -y")
            if yum_stat != 0:
                pytest.skip(msg="Not found FIO,test skip", allow_module_level=True)
        self.bucketid = consts.s3["bucketid"]
        self.mirrorid = consts.s3["mirrorid"]
        self.fio = "fio -iodepth=16 -numjobs=1 -bs=4K -ioengine=psync -group_report -name=autotest -size={} \
        -directory={} -nrfiles={} -direct"
        # 添加bucket
        self.testdir = "autotest_tiering_v66_%s" % time.strftime("%m-%d-%H%M%S")
        self.acl_id = "autotest"
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.mountdir = consts.MOUNT_DIR

        bucket_add = self.get_cli(self, "bucket_add", consts.s3["hostname"], consts.s3["protocol"],
                                  consts.s3["bucketname"],
                                  consts.s3["uri_style"], consts.s3["region"], consts.s3["access_key"],
                                  consts.s3["secret_access_key"],
                                  consts.s3["token"], consts.s3["type"], consts.s3["bucketid"])
        # 添加之前先删除下，有可能有残留
        bucket_del = self.get_cli(self, "bucket_del", consts.s3["bucketid"])
        self.sshserver.ssh_exec(bucket_del)
        add_stat, _ = self.sshserver.ssh_exec(bucket_add)
        if add_stat != 0:
            pytest.skip(msg="add bucket failed, skip", allow_module_level=True)
        # 添加mirror
        mirror_add = self.get_cli(self, "bucket_add", consts.s3["hostname"], consts.s3["protocol"],
                                  consts.s3["bucketmirror"],
                                  consts.s3["uri_style"], consts.s3["region"], consts.s3["access_key"],
                                  consts.s3["secret_access_key"],
                                  consts.s3["token"], consts.s3["type"], consts.s3["mirrorid"])
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["mirrorid"]))
        add_stat, _ = self.sshserver.ssh_exec(mirror_add)
        if add_stat != 0:
            pytest.skip(msg="add bucket failed, test skip", allow_module_level=True)

    def teardown_class(self):
        bucket_del = self.get_cli(self, "bucket_del", consts.s3["bucketid"])
        self.sshserver.ssh_exec(bucket_del)
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["mirrorid"]))

        self.sshclient1.close_connect()
        self.sshserver.close_connect()

    def test_concurrency_del(self, get_data):
        """
        caseID: 3383 校验并发删除不同目录下文件有效
        """
        tier_id = "9999"
        try:
            layers = ""
            # 本次测试依赖fio
            # fio_stat, _ = self.sshclient1.ssh_exec("fio --version")
            # if fio_stat != 0:
            #     pytest.skip(msg="fio not installed. test skip.")
            # 创建目录并添加分层
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00", tier_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."

            self.sshserver.ssh_exec(self.get_cli("acl_id_add", self.testdir, self.acl_id, "rw"))
            mount_stat = client_mount(self.client1, subdir=self.testdir, aclid=self.acl_id)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed. test skip.")
            # 创建测试目录
            subdir1 = "subdir1"
            subdir2 = "subdir2"
            mk_stat1, _ = self.sshclient1.ssh_exec("mkdir -p " + os.path.join(consts.MOUNT_DIR, subdir1))
            mk_stat2, _ = self.sshclient1.ssh_exec("mkdir -p " + os.path.join(consts.MOUNT_DIR, subdir2))

            # fio 创建测试数据
            fio_cmd1 = "fio -iodepth=16 -numjobs=1 -size=10M -bs=1M -ioengine=sync -rw=write -direct=1 " + \
                       "-directory=%s -name=autotest -nrfiles=5" % os.path.join(consts.MOUNT_DIR, subdir1)
            fio_cmd2 = "fio -iodepth=16 -numjobs=1 -size=40k -bs=4k -ioengine=sync -rw=write -direct=1 " + \
                       "-directory=%s -name=autotest -nrfiles=5" % os.path.join(consts.MOUNT_DIR, subdir2)
            fio_stat1, _ = self.sshclient1.ssh_exec(fio_cmd1)
            fio_stat2, _ = self.sshclient1.ssh_exec(fio_cmd2)
            # 客户端业务执行
            fio_cmd3 = "fio -iodepth=16 -numjobs=1 -size=10M -bs=4K -ioengine=sync -runtime=600 -time_based -rw=rw " + \
                       "-rate_iops=10,10 -direct=1 -filename=%s/file -name=autotest &" % consts.MOUNT_DIR
            self.sshclient1.ssh_exec(fio_cmd3)
            logger.info("sleep 60s.")
            sleep(60)
            # # 开启gzip
            # gzip_stat, _ = self.sshserver.ssh_exec(self.get_cli("s3_gzip", "true"))
            # assert gzip_stat == 0, "open s3 gzip failed."
            # 执行业务上传操作
            flush_cmd = self.get_cli("tiering_flush", tier_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            logger.info("sleep 10s.")
            sleep(10)
            # 查看文件上传状态
            _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f|grep -v file" % (consts.MOUNT_DIR, self.testdir))

            for f in files.split("\n"):

                entry_cmd = self.get_cli("get_entry", f)

                for i in range(10):
                    _, layers = self.sshserver.ssh_exec(entry_cmd)
                    layers = re.findall("Data Location: (.*)\n", layers)
                    layers = "".join(layers)

                    if layers == "S3":
                        logger.info("file: %s put S3 success." % f)
                        break
                    else:
                        logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                        sleep(5)
                        continue
                else:
                    logger.error("file: %s put s3 timeout." % f)
                    break
                    # assert layer == "S3"

            # 删除测试目录
            rm_stat, _ = self.sshclient1.ssh_exec("rm -fr %s/*" % consts.MOUNT_DIR)
            del_stat, _ = self.sshserver.ssh_exec(self.get_cli('tiering_del', tier_id))

            assert add_stat == 0, "add tiering failed."
            assert mk_stat1 == 0, "mkdir failed."
            assert mk_stat2 == 0, "mkdir failed."
            assert fio_stat1 == 0, "fio run failed."
            assert fio_stat2 == 0, "fio run failed."
            assert flush_stat == 0, "tiering flush cmd failed."
            assert layers == "S3", "put s3 failed."
            assert rm_stat == 0, "remove s3 file failed."
            assert del_stat == 0, "del tiering id %s failed." % tier_id

        finally:
            self.sshclient1.ssh_exec("ps axu|grep fio|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
            self.sshserver.ssh_exec(self.get_cli("acl_id_del", self.testdir, self.acl_id))
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tier_id))

    def test_del_dir(self, get_data):
        """
        caseID: 3315 校验后端单独删除分层关系（tire id），目录非空删除失败
        """
        # 创建目录并添加分层
        tiering_id = "9999"
        try:
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00,01:00,05:00",
                                    tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            # 写入数据
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/file1 bs=1M count=100" % self.testpath)
            # 删除分层目录
            del_stat, _ = self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

            # 校验删除目录不成功
            assert del_stat != 0, "del tiering dir failed."

        finally:
            self.sshserver.ssh_exec('rm -fr %s/file1' % self.testpath)
            self.sshserver.ssh_exec('rm -fr %s' % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_17th_dir(self, get_data):
        """
        caseID: 3314 校验17层目录添加对象类型及策略失败
        """
        tiering_id = "999"
        subdir = "/d2/d3/d4/d5/d6/d7/d8/d9/d10/d11/d12/d13/d14/d15/d16/d17"
        testdir = self.testdir + "/" + subdir
        testpath = self.testpath + "/" + subdir
        try:
            self.sshserver.ssh_exec("mkdir -p " + testpath)
            add_tier = self.get_cli("mirror_add", testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00,01:00,05:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            # 预期add tiering 失败。
            assert add_stat != 0, "add tiering failed."

        finally:
            self.sshserver.ssh_exec('rm -fr %s' % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_add_nondir(self, get_data):
        """
        caseID: 3313 校验非空目录创建分层，该目录下的历史数据（建立分层前的文件）上传S3失败
        """
        tiering_id = "9999"
        testfile = self.testdir + "/file1"
        testpath = self.testpath + "/file1"
        dd = "dd if=/dev/zero of=%s bs=1M count=1 oflag=direct" % testpath
        layer_res = ""
        layer = ""
        try:
            # 先写入数据
            self.sshserver.ssh_exec("mkdir -p %s" % self.testpath)
            self.sshserver.ssh_exec(dd)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00,01:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            logger.info("sleep 70.")
            sleep(70)
            # 执行立即上传操作
            s3_flush = self.get_cli("tiering_flush", tiering_id)
            self.sshserver.ssh_exec(s3_flush)
            # 查询上传不成功
            entry_cmd = self.get_cli("get_entry", testfile)

            for i in range(5):
                _, layer_res = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer_res)
                layer = "".join(layer)

                if layer == "Local":
                    logger.info("check file: %s in Local." % testfile)
                    break
                else:
                    logger.info("check file: %s not in Local, retry times: %s." % (testfile, str(i + 1)))
                    sleep(5)
                    continue
            tierid = re.findall("TieringID: (.*)\n", layer_res)
            tierid = "".join(tierid)
            logger.info("file %s: TieringID is %s." % (testfile, tierid))

            assert tierid == "0", "TieringID not 0."
            assert layer == "Local", "file in Local."

        finally:
            # 清除测试配置
            self.sshserver.ssh_exec('rm -fr %s' % testpath)
            self.sshserver.ssh_exec('rm -fr %s' % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_del_tiering(self, get_data):
        """
        caseID:  3287 校验后端删除目录时，分层关系、时间策略和目录下所有文件删除成功
        """
        tiering_id = "9999"
        try:
            # 新建分层关系
            self.sshserver.ssh_exec("mkdir -p %s" % self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00,01:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            # 写入数据
            dd1 = "dd if=/dev/zero of=%s/file1 bs=1M count=1 oflag=direct" % self.testpath
            self.sshserver.ssh_exec(dd1)
            dd2 = "dd if=/dev/zero of=%s/file2 bs=4k count=1 oflag=direct" % self.testpath
            self.sshserver.ssh_exec(dd2)
            mkdir = "mkdir -p %s/dir1" % self.testpath
            self.sshserver.ssh_exec(mkdir)
            # 删除目录
            sleep(10)
            rmstat, _ = self.sshserver.ssh_exec("rm -fr " + self.testpath)

            # 查询tiering是否还存在
            liststat, _ = self.sshserver.ssh_exec(
                self.get_cli("tiering_list") + "|awk '{print $3}'|grep " + self.testdir)
            # 检验结果正确性
            assert rmstat == 0, "rm tiering path success."
            assert liststat != 0, "list tiering dir failed."

        finally:
            # 确保tiering被正确删除，不会影响其他case执行
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_rename_dir(self, get_data):
        """
        caseID:  3285 校验rename目录名称，对象存储及策略不变，list中path为更改后的名称
        """
        tiering_id = "9999"
        new_testdir = self.testdir + "_new"
        new_testpath = self.testpath + "_new"
        testfile = new_testpath + "/file1"
        layer = ""
        try:
            # 新建分层关系
            self.sshserver.ssh_exec("mkdir -p %s" % self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "60",
                                    "00:00,01:00", tiering_id)
            self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            sleep(10)
            # 重命名分层目录
            self.sshserver.ssh_exec("mv %s %s" % (self.testpath, new_testpath))
            # 查询目录重命名成功
            stat_tier, _ = self.sshserver.ssh_exec(
                self.get_cli("tiering_list") + "|grep -E \"%s|%s\"" % (new_testdir, tiering_id))
            assert stat_tier == 0, "rename tiering dir failed."
            # 写入数据
            dd = "dd if=/dev/zero of=%s bs=1M count=1 oflag=direct" % testfile
            _, dd_res = self.sshserver.ssh_exec(dd)
            # 上传前检验md5值
            _, md5_1 = self.sshserver.ssh_exec("md5sum " + testfile)
            # 关闭gzip
            # gzip_stat, _ = self.sshserver.ssh_exec(self.get_cli("s3_gzip", "false"))
            # assert gzip_stat == 0, "open s3 gzip failed."
            # 执行上传操作
            logger.info("sleep 60s.")
            sleep(60)
            s3_flush = self.get_cli("tiering_flush", tiering_id)
            self.sshserver.ssh_exec(s3_flush)
            # 检验文件是否上传成功
            entry_cmd = self.get_cli("get_entry", new_testdir + "/file1")
            for i in range(10):
                _, layer = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer)
                layer = "".join(layer)

                if layer == "S3":
                    logger.info("check file: %s in S3." % testfile)
                    break
                else:
                    logger.info("check file: %s not in S3, retry times: %s." % (testfile, str(i + 1)))
                    sleep(5)
                    continue

            assert layer == "S3", "upload s3 failed."
            _, md5_2 = self.sshserver.ssh_exec("md5sum " + testfile)
            assert md5_1 == md5_2, "file md5sum error."

        finally:
            # gzip_stat, _ = self.sshserver.ssh_exec(self.get_cli("s3_gzip", "false"))
            self.sshserver.ssh_exec("rm -fr " + testfile)
            self.sshserver.ssh_exec("rm -fr " + new_testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    #@pytest.mark.skip
    def test_subdir_inherit(self, get_data):
        """
        caseID: 3281 校验子目录设置不同的对象存储，子子目录跟随子目录
        """
        tiering_id = "9999"
        layer = ""
        try:
            # 查询当前时间
            _, current_time = self.sshserver.ssh_exec("date '+%H:%M'")
            hour = current_time.split(":")[0]
            minutes = current_time.split(":")[1]
            # 将时间调整到两分钟之后
            times = int(hour) * 60 + int(minutes) + 1
            hour_later = str(times // 60)
            minutes_later = str(times % 60)
            # 如果需要两位数，如果为单位的话，需要加上零
            if len(minutes_later) != 2:
                minutes_later = "0" + minutes_later

            if len(hour_later) != 2:
                hour_later = "0" + hour_later

            flush_time = hour_later + ":" + minutes_later
            # 设置tiering
            self.sshserver.ssh_exec("mkdir -p %s" % self.testpath)
            add_tier1 = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "600",
                                     "00:00,01:00", "998")
            add_stat1, _ = self.sshserver.ssh_exec(add_tier1)
            assert add_stat1 == 0, "add tiering failed."
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            sleep(2)
            self.sshserver.ssh_exec("mkdir -p %s/dir1" % self.testpath)
            add_tier2 = self.get_cli("mirror_add", self.testdir + "/dir1", consts.s3["bucketid"], self.mirrorid,
                                     "30", flush_time, tiering_id)
            add_stat2, _ = self.sshserver.ssh_exec(add_tier2)
            assert add_stat2 == 0, "add tiering failed."
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir + "/dir1", get_data))
            assert stat == 0, "set mode failed."
            # 数据写入
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir2" % self.testpath)
            dd = "dd if=/dev/zero of=%s/dir1/dir2/file1 bs=1M count=2 oflag=direct" % self.testpath
            self.sshserver.ssh_exec(dd)
            # 等待文件上传,检验文件上传情况
            sleep(120)
            entry_cmd = self.get_cli("get_entry", self.testdir + "/dir1/dir2/file1")
            for i in range(20):
                _, layer = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer)
                layer = "".join(layer)

                if layer == "S3":
                    logger.info("check file: %s/dir1/dir2/file1 in S3." % self.testdir)
                    break
                else:
                    logger.info(
                        "check file: %s/dir1/dir2/file1 not in S3, retry times: %s." % (self.testdir, str(i + 1)))
                    sleep(5)
                    continue

            assert layer == "S3", "upload s3 failed."

        finally:
            self.sshserver.ssh_exec("rm -fr %s" % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))
            self.sshserver.ssh_exec(self.get_cli('tiering_del', "998"))

    #@pytest.mark.skip
    def test_add_subdir(self, get_data):
        """
        caseID:  3280 校验父目录设置了下刷目录，子目录新增新对象存储
        """
        layer = ""
        parent_id = "9999"
        child_id = "9998"
        parent_bid = consts.s3['bucketid']
        child_bid = consts.s3['bucketid']

        try:
            _, current_time = self.sshserver.ssh_exec("date '+%H:%M'")
            hour = current_time.split(":")[0]
            minutes = current_time.split(":")[1]
            # 将时间调整到两分钟和四分钟后作为父子目录的冷数据时间。
            flush_times = []
            for num in (1, 2):
                times = int(hour) * 60 + int(minutes) + num
                hour_later = str(times // 60)
                minutes_later = str(times % 60)
                if len(minutes_later) != 2:
                    minutes_later = "0" + minutes_later
                if len(hour_later) != 2:
                    hour_later = "0" + hour_later
                flush_time = hour_later + ":" + minutes_later
                flush_times.append(flush_time)
            # 创建测试目录
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_parent = self.get_cli("mirror_add", self.testdir, parent_bid, consts.s3["mirrorid"], "30",
                                      flush_times[0], parent_id)
            # 添加tiering
            add_stat1, _ = self.sshserver.ssh_exec(add_parent)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            sleep(2)
            # 添加子目录tiering
            self.sshserver.ssh_exec("mkdir -p " + self.testpath + "/dir1")
            add_child = self.get_cli("mirror_add", self.testdir + "/dir1", child_bid, consts.s3["mirrorid"], "30",
                                     flush_times[1], child_id)
            add_stat2, _ = self.sshserver.ssh_exec(add_child)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir + "/dir1", get_data))
            assert stat == 0, "set mode failed."

            assert add_stat1 == 0, "add tiering failed"
            assert add_stat2 == 0, "add tiering failed"
            sleep(2)
            # 写入数据
            dd = "dd if=/dev/zero of={}/file1 bs=1M count=20 oflag=direct"
            _, dd_res1 = self.sshserver.ssh_exec(dd.format(self.testpath))
            _, dd_res2 = self.sshserver.ssh_exec(dd.format(self.testpath + "/dir1"))
            assert "copied" in dd_res1, "dd failed"
            assert "copied" in dd_res2, "dd failed"
            # 检验md5值
            _, md5_parent_old = self.sshserver.ssh_exec("md5sum %s/file1" % self.testpath)
            _, md5_child_old = self.sshserver.ssh_exec("md5sum %s/dir1/file1" % self.testpath)
            # 查看集群当前使用容量
            df_cmd = "df -T|awk '{if($7==\"%s\")print $4}'" % consts.MOUNT_DIR
            _, capa_old = self.sshserver.ssh_exec(df_cmd)
            # 检查父目录文件上传到s3成功
            logger.info("sleep 120s.")
            sleep(120)
            entry_cmd = self.get_cli("get_entry", self.testdir + "/file1")
            for i in range(20):
                _, layer = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer)
                layer = "".join(layer)

                if layer == "S3":
                    logger.info("check file: %s in S3." % self.testdir + "/file1")
                    break
                else:
                    logger.info("check file: %s not in S3, retry times: %s." % (self.testdir + "/file1", str(i + 1)))
                    sleep(5)
                    continue
            # 检验子目录的此时未上传到s3
            assert layer == "S3", "file not in S3"
            entry_child = self.get_cli("get_entry", self.testdir + "/dir1/file1")
            _, layer_child = self.sshserver.ssh_exec(entry_child)
            layer_child = re.findall("Data Location: (.*)\n", layer_child)
            layer_child = "".join(layer_child)
            assert layer_child == "Local", "file not in local"
            # 子目录冷数据上传时间到后，上传成功
            logger.info("sleep 30s.")
            sleep(60)
            entry_cmd = self.get_cli("get_entry", self.testdir + "/dir1/file1")
            for i in range(20):
                _, layer = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer)
                layer = "".join(layer)

                if layer == "S3":
                    logger.info("check file: %s in S3." % self.testdir + "/dir1/file1")
                    break
                else:
                    logger.info(
                        "check file: %s not in S3, retry times: %s." % (self.testdir + "/dir1/file1", str(i + 1)))
                    sleep(5)
                    continue
            assert layer == "S3", "file not in S3"
            # 上传完成容量减少
            sleep(20)
            _, capa_new = self.sshserver.ssh_exec(df_cmd)
            assert capa_new <= capa_old, "No reduction in capacity"
            # 检验下载后的md5sum
            _, md5_parent_new = self.sshserver.ssh_exec("md5sum %s/file1" % self.testpath)
            _, md5_child_new = self.sshserver.ssh_exec("md5sum %s/dir1/file1" % self.testpath)
            assert md5_child_old == md5_child_new, "md5 mismatch"
            assert md5_parent_old == md5_parent_new, "md5 mismatch"

        finally:
            self.sshserver.ssh_exec("rm -fr %s" % self.testpath + "/dir1")
            self.sshserver.ssh_exec("rm -fr %s" % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', parent_id))
            self.sshserver.ssh_exec(self.get_cli('tiering_del', child_id))

    @pytest.mark.skip
    def test_tiering_quota(self, get_data):
        """
        3678 （非空目录quota）部分文件已上传至s3设置后统计正确
        2451 校验下载过程中，有上传任务有效
        """
        tiering_id = "9999"
        layer = ""
        try:
            # 本次测试依赖fio
            fio_stat, _ = self.sshclient1.ssh_exec("fio --version")
            if fio_stat != 0:
                pytest.skip(msg="fio not installed. test skip.")
            # 添加tiering分层
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "1",
                                    "00:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            assert add_stat == 0, "add tiering failed"
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            # 客户端挂载
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, "*", "rw"))
            mount_stat = client_mount(self.client1, subdir=self.testdir)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed. test skip.")
            # 创建测试数据
            self.sshclient1.ssh_exec("mkdir -p %s/dir1" % consts.MOUNT_DIR)
            self.sshclient1.ssh_exec("mkdir -p %s/dir2" % consts.MOUNT_DIR)
            fio_cmd1 = "fio -iodepth=16 -numjobs=1 -size=100M -bs=1M -ioengine=sync -rw=write -direct=1 " + \
                       "-directory=%s/dir1 -name=autotest -nrfiles=5" % consts.MOUNT_DIR
            fio_cmd2 = "fio -iodepth=16 -numjobs=1 -size=100k -bs=4k -ioengine=sync -rw=write -direct=1 " + \
                       "-directory=%s/dir2 -name=autotest -nrfiles=5" % consts.MOUNT_DIR
            fio_stat1, _ = self.sshclient1.ssh_exec(fio_cmd1)
            assert fio_stat1 == 0, "fio run failed."
            sleep(10)
            # 上传数据
            flush_cmd = self.get_cli("tiering_flush", tiering_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            logger.info("sleep 10s.")
            sleep(10)
            # 查看文件上传状态
            _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f|grep -v file" % (consts.MOUNT_DIR,
                                                                                        self.testdir + "/dir1"))

            for f in files.split("\n"):

                entry_cmd = self.get_cli("get_entry", f)

                for i in range(30):
                    _, layer = self.sshserver.ssh_exec(entry_cmd)
                    layer = re.findall("Data Location: (.*)\n", layer)
                    layer = "".join(layer)

                    if layer == "S3":
                        logger.info("file: %s put S3 success." % f)
                        break
                    else:
                        logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                        sleep(5)
                        continue
                else:
                    logger.error("file: %s put s3 timeout." % f)
                    break
            assert layer == "S3", "put s3 failed."
            # fio 再次写入数据
            fio_stat2, _ = self.sshclient1.ssh_exec(fio_cmd2)
            assert fio_stat2 == 0, "fio run failed."
            # 设置quota
            quota_stat, _ = self.sshserver.ssh_exec(self.get_cli("nquota_add", self.testdir, "100M", "13"))
            assert quota_stat == 0, "add quota failed."
            sleep(2)
            # 检查quota list是否正确
            list_stat, list_res = self.sshserver.ssh_exec(self.get_cli("quota_list_verbose", self.testdir))
            list_res = list_res.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "13"

            # 新增校验点 caseID 2451 校验下载过程中，有上传任务有效
            # 下载dir1子目录的文件
            self.sshclient1.ssh_exec("md5sum %s/dir1/* &" % consts.MOUNT_DIR)
            # 同时触发dir2目录下文件上传
            flush_cmd = self.get_cli("tiering_flush", tiering_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            logger.info("sleep 10s.")
            sleep(10)
            # 查看文件上传状态
            _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f|grep -v file" % (consts.MOUNT_DIR,
                                                                                        self.testdir + "/dir2"))

            for f in files.split("\n"):

                entry_cmd = self.get_cli("get_entry", f)

                for i in range(30):
                    _, layer = self.sshserver.ssh_exec(entry_cmd)
                    layer = re.findall("Data Location: (.*)\n", layer)
                    layer = "".join(layer)

                    if layer == "S3":
                        logger.info("file: %s put S3 success." % f)
                        break
                    else:
                        logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                        sleep(5)
                        continue
                else:
                    logger.error("file: %s put s3 timeout." % f)
                    break
            assert layer == "S3", "put s3 failed."
            # 检查dir1的文件是否下载成功
            sleep(10)
            # 查看文件上传状态
            _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f|grep -v file" % (consts.MOUNT_DIR,
                                                                                        self.testdir + "/dir1"))

            for f in files.split("\n"):

                entry_cmd = self.get_cli("get_entry", f)

                for i in range(30):
                    _, layer = self.sshserver.ssh_exec(entry_cmd)
                    layer = re.findall("Data Location: (.*)\n", layer)
                    layer = "".join(layer)

                    if get_data == "0" and layer == "Local":
                        logger.info("file: %s download S3 success." % f)
                        break
                    elif get_data == "1" and layer == "Mixed":
                        logger.info("File: %s download S3 success." % f)
                        break
                    else:
                        logger.warning("file: %s download S3 failed, retry times: %s" % (f, str(i + 1)))
                        sleep(5)
                        continue
                else:
                    logger.error("file: %s download s3 timeout." % f)
                    break
            if get_data == "0":
                assert layer == "Local", "download s3 failed."
            else:
                assert layer == "Mixed", "download s3 failed."
            # 检验再次写入失败
            sleep(5)
            dd_stat, dd_res = self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/file1 bs=1M count=100 oflag=direct" % consts.MOUNT_DIR)
            assert "exceeded" in dd_res, "quota not exceeded"
            # 删除quota配置
            del_stat, _ = self.sshserver.ssh_exec(self.get_cli("quota_remove", self.testdir))
            assert del_stat == 0, "del quota failed."

        finally:
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, "*"))
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_sixteen_dir(self, get_data):
        """
        3275 校验16层quota目录及qos目录添加对象类型及策略有效
        """
        tiering_id = "9999"
        layer = ""
        try:
            # 创建测试数据
            test_subdir = self.testdir + "/d1/d2/d3/d4/d5/d6/d7/d8/d9/d10/d11/d12/d13/d14/d15"
            test_subpath = self.testpath + "/d1/d2/d3/d4/d5/d6/d7/d8/d9/d10/d11/d12/d13/d14/d15"
            mkstat, _ = self.sshserver.ssh_exec("mkdir -p " + test_subpath)
            assert mkstat == 0, "mkdir failed."
            # 创建quota和qos
            qos, _ = self.sshserver.ssh_exec(self.get_cli("qos_total_set", test_subdir, "2G", "99999", "0"))
            assert qos == 0, "add qos failed"
            quota, _ = self.sshserver.ssh_exec(self.get_cli("nquota_add", test_subdir, "2G", "2000"))
            assert quota == 0, "add quota failed"
            # 添加分层
            add_tier = self.get_cli("mirror_add", test_subdir, consts.s3["bucketid"], consts.s3["mirrorid"], "1",
                                    "00:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            assert add_stat == 0, "add tiering failed"
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", test_subdir, get_data))
            assert stat == 0, "set mode failed."
            # 写入数据
            self.sshserver.ssh_exec("df -T|grep /mnt/yrfs|awk '{print $4}'")
            _, dd_res = self.sshserver.ssh_exec(
                "dd if=/dev/zero of=%s/file1 bs=1M count=10 oflag=direct" % test_subpath)
            assert "copied" in dd_res
            sleep(10)
            # 检查集群容量
            _, start_df = self.sshserver.ssh_exec("df -T|grep /mnt/yrfs|awk '{print $4}'")
            # 上传数据
            flush_cmd = self.get_cli("tiering_flush", tiering_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            logger.info("sleep 5s.")
            sleep(5)
            # 检查文件是否被上传
            f = test_subdir + "/file1"
            entry_cmd = self.get_cli("get_entry", f)
            for i in range(10):
                _, layer = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", layer)
                layer = "".join(layer)

                if layer == "S3":
                    logger.info("file: %s put S3 success." % f)
                    break
                else:
                    logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                    sleep(5)
                    continue

            assert layer == "S3", "put s3 failed."
            # 检查集群容量
            sleep(10)
            _, end_df = self.sshserver.ssh_exec("df -T|grep /mnt/yrfs|awk '{print $4}'")
            assert int(start_df) > int(end_df), "capacity not decreased"
            # 删除上传文件
            rm_stat, _ = self.sshserver.ssh_exec("rm -fr %s/file1" % test_subpath)
            assert rm_stat == 0, "remove file failed"

        finally:
            sleep(2)
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_upload_del(self, get_data):
        """
        3704 校验上传中，删除文件成功
        """
        tiering_id = "9999"
        bucket_id = consts.s3['bucketid']
        try:
            # 添加分层
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, bucket_id, consts.s3["mirrorid"], "1", "00:00",
                                    tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            sleep(2)
            # 客户端挂载
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", "", "*", "rw"))
            mount_stat = client_mount(self.client1)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed. test skip.")
            # 写入数据
            fio_cmd = "fio -iodepth=16 -numjobs=8 -bs=1M -ioengine=psync -group_report -name=autotest -size=2G " \
                      "-directory={} -nrfiles=50 -rw=write".format(self.testpath)
            stat, _ = self.sshclient1.ssh_exec(fio_cmd)
            assert stat == 0, "fio failed."
            sleep(5)
            # 执行s3上传操作
            flush_cmd = self.get_cli("tiering_flush", tiering_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            logger.info("sleep 10s.")
            sleep(10)
            # 执行部分文件删除操作
            stat, _ = self.sshserver.ssh_exec("cd %s&&ls|head -n 100|xargs rm -fr" % self.testpath)
            assert stat == 0, "delete upload file failed."
            # 删除全部文件
            stat, _ = self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)
            assert stat == 0, "delete s3 file failed."

        finally:
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", "", "*"))
            self.sshserver.ssh_exec('rm -fr %s' % self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_small_file_policy(self, get_data):
        """
        3766 校验新建目录对小文件设置不同得策略上传下载有效
        """
        tiering_id = "9999"
        bucket_id = consts.s3['bucketid']
        policy = "4k:5,512k:20,1M:500,20M:500,1G:2000"
        dd = "dd if=/dev/zero of={} bs={} count=1 oflag=direct"
        try:
            # 添加分层
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, bucket_id, consts.s3["mirrorid"], "1", "00:00",
                                    tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            # 设置小文件分层策略
            stat, _ = self.sshserver.ssh_exec(self.get_cli("update_policy", tiering_id, policy))
            assert stat == 0, "set policy failed."
            sleep(2)
            # 数据写入 4k，512K,1M文件:
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            self.sshserver.ssh_exec(dd.format(self.testpath + "/4K", "4K"))
            self.sshserver.ssh_exec(dd.format(self.testpath + "/512K", "512K"))
            self.sshserver.ssh_exec(dd.format(self.testpath + "/1M", "1M"))
            # 执行flush操作
            sleep(10)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            assert flush_stat == 0, "flush tiering failed."
            # 检查4K文件上传的正确性
            check_layer(fname=self.testdir + "/4K", layer="S3", tierid=tiering_id)
            check_layer(fname=self.testdir + "/512K", layer="Local", tierid=tiering_id)
            check_layer(fname=self.testdir + "/1M", layer="Local", tierid=tiering_id)
            # 检查512K文件上传正确
            sleep(30)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            assert flush_stat == 0, "flush tiering failed."
            check_layer(fname=self.testdir + "/4K", layer="S3", tierid=tiering_id)
            check_layer(fname=self.testdir + "/512K", layer="S3", tierid=tiering_id)
            check_layer(fname=self.testdir + "/1M", layer="Local", tierid=tiering_id)

        finally:
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_invalid_key(self, get_data):
        """
        2428 校验前后台修改密钥,上传下载失败
        """
        tiering_id = "9999"
        dd = "dd if=/dev/zero of={} bs={} count=1 oflag=direct"
        bucketid = consts.s3["bucketid"]
        ackey = consts.s3["access_key"]
        acsecret = consts.s3["secret_access_key"]
        filename = "autotest_1M"
        update_cmd = "yrcli --bucket --op=update --bucketid={} --access_key={} --secret_access_key={}"
        # 添加分层
        try:
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, bucketid, consts.s3["mirrorid"], "1", "00:00",
                                    tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置tiering mode
            self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            # 创建测试文件
            self.sshserver.ssh_exec(dd.format(self.testpath + "/" + filename, "1M"))
            # 修改tiering key
            stat, _ = self.sshserver.ssh_exec(update_cmd.format(bucketid, ackey, "fdsjgjjbjbjgjjfls"))
            assert stat != 0, "Expect update bucket failed."

        finally:
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))
            self.sshserver.ssh_exec(update_cmd.format(bucketid, ackey, acsecret))

    def test_truncate_policy(self, get_data):
        """
        3768 校验修改文件大小，按照文件属性大小上传
        """
        tiering_id = "9999"
        dd = "cd %s&&dd if=/dev/zero of={} bs={} count=1 oflag=direct" % consts.MOUNT_DIR
        dd_append = "cd %s&&dd if=/dev/zero of={} bs=1k count={} oflag=append conv=notrunc" % consts.MOUNT_DIR
        f_4k = self.testdir + "/autotest_4k"
        f_100k = self.testdir + "/autotest_100k"
        f_512k = self.testdir + "/autotest_512k"
        try:
            # 添加分层
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            add_tier = self.get_cli("mirror_add", self.testdir, self.bucketid, self.mirrorid, "1", "00:00",
                                    tiering_id) + " --mode=%s --policy=4k:200,100k:4,512k:8" % get_data
            self.sshserver.ssh_exec(add_tier)
            # 创建测试文件
            self.sshserver.ssh_exec(dd.format(f_4k, "4k"))
            self.sshserver.ssh_exec(dd.format(f_100k, "100k"))
            self.sshserver.ssh_exec(dd.format(f_512k, "512k"))
            # 对文件进行追加写
            self.sshserver.ssh_exec(dd_append.format(f_4k, 96))
            self.sshserver.ssh_exec(dd_append.format(f_100k, 408))
            sleep(10)
            # 上传文件
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            sleep(10)
            if get_data == "0":
                mode = "s3normal"
            else:
                mode = "s3seek"
            check_layer(f_4k, layer="S3", tierid=tiering_id, mode=mode)
            check_layer(f_100k, layer="S3", tierid=tiering_id, mode=mode)
            check_layer(f_512k, layer="S3", tierid=tiering_id, mode=mode)
        finally:
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_downloading_rw(self, get_data):
        """
        2450 （自动化）校验下载过程中，读写非下载文件，未hang

        """
        tiering_id = "9999"
        bucket_id = consts.s3['bucketid']
        try:
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            # 客户端挂载
            mount_stat = client_mount(self.client1, acl_add=True)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed. test skip.")
            # 添加分层
            add_tier = self.get_cli("mirror_add", self.testdir, bucket_id, self.mirrorid, "1", "00:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            sleep(2)
            # 写入数据
            fio_cmd = "fio -iodepth=16 -numjobs=1 -bs=1M -ioengine=psync -group_report -name=autotest -filesize=2G " \
                      "-directory={} -nrfiles=1 -rw=write".format(self.testpath)
            self.sshclient1.ssh_exec(fio_cmd)
            fio_cmd = "fio -iodepth=16 -numjobs=8 -bs=4K -ioengine=psync -group_report -name=autotest2 -filesize=10K " \
                      "-directory={} -nrfiles=50 -rw=write".format(self.testpath)
            self.sshclient1.ssh_exec(fio_cmd)
            _, md1 = self.sshclient1.ssh_exec("md5sum " + self.testpath + "/autotest.0.0")
            sleep(5)
            # 执行上传至s3
            flush_cmd = self.get_cli("tiering_flush", tiering_id)
            flush_stat, _ = self.sshserver.ssh_exec(flush_cmd)
            sleep(60)
            # 下载文件
            self.sshclient1.ssh_exec("md5sum " + self.testpath + "/autotest.0.0" + " > /tmp/autotest_md5 &")
            # ls其他文件
            stat, _ = self.sshclient1.ssh_exec("ls %s > /dev/nulll 2>&1" % self.testpath)
            assert stat == 0, "ls file failed."
            # 校验md5sum是否匹配
            for i in range(100):
                stat, _ = self.sshclient1.ssh_exec("ps axu|grep md5sum|grep -v grep")
                if stat == 0:
                    logger.info("wait md5sum exit, sleep 10")
                    sleep(10)
                else:
                    break
            _, md2 = self.sshclient1.ssh_exec("cat /tmp/autotest_md5")
            assert md1 == md2, "md5sum mismatching."
        finally:
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_uploading_delete(self, get_data):
        """
        2482 校验删除过程中，有上传文件有效,2481 校验删除过程中，读写其他目录文件正常
        """
        tiering_id = "9006"
        bucket_id = consts.s3['bucketid']
        path1 = self.testpath + "/dir1"
        path2 = self.testpath + "/dir2"
        path3 = self.testpath + "/dir3"
        testfile = self.testdir + "/dir4/file1"
        fio_cmd = "fio -iodepth=16 -numjobs={} -bs=4K -ioengine=psync -group_report -name={} -filesize={} " + \
                  "-directory={} -nrfiles={} -rw={}"
        try:
            # 创建测试数据
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            # 添加分层
            add_tier = self.get_cli("mirror_add", self.testdir, bucket_id, self.mirrorid, "1", "00:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            # 设置s3模式
            stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            assert stat == 0, "set mode failed."
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..4}" % self.testpath)
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "Client mount failed."
            self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "4k", path1, "5", "write"))
            self.sshclient1.ssh_exec(fio_cmd.format("1", "autotest", "500M", path2, "1", "write"))
            self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "512K", path3, "8", "write"))
            # 执行文件上传
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            # 再次写入文件
            self.sshclient1.ssh_exec(
                "cd %s&&dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % (self.mountdir, testfile))
            # 等待文件上传
            sleep(90)
            # 再次执行上传文件并删除已上传的文件
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            self.sshclient1.ssh_exec("rm -fr %s &" % path1)
            self.sshclient1.ssh_exec("rm -fr %s &" % path2)
            self.sshclient1.ssh_exec("ls -al %s/* > /dev/null 2>&1" % self.testpath)
            self.sshclient1.ssh_exec("rm -fr %s &" % path3)
            # 检查第二批文件上传状态
            sleep(30)
            check_layer(testfile, "S3", tiering_id)
            self.sshclient1.ssh_exec('ps axu|grep -E "\'rm -fr\'|\'ls -al\'"|grep -v grep|xargs -I {} kill -9 {}')
            # stat, _ = self.sshclient1.ssh_exec('ps axu|grep -E "\'rm -fr\'|\'ls -al\'"|grep -v grep')
            # assert stat == 0, "rm or ls process hung."
            # 执行fsck操作
            # stat = fsck()
            # assert stat == 0, "fsck check failed."
        finally:
            self.sshclient1.ssh_exec('ps axu|grep -E "\'rm -fr\'|\'ls -al\'"|grep -v grep|xargs -I {} kill -9 {}')
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    def test_multi_download(self, get_data):
        """
        2449 校验并发下载多种文件类型，下载成功
        """
        tiering_id = "9006"
        path1 = self.testpath + "file1"
        path2 = self.testpath + "/file2"
        path3 = self.testpath + "/file3"
        try:
            # 客户端挂载
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            stat = client_mount(self.client1, acl_add=True)
            assert stat == 0, "client mount failed."
            # 添加分层
            add_tier = self.get_cli("mirror_add", self.testdir, self.bucketid, self.mirrorid, "1", "00:00", tiering_id)
            add_stat, _ = self.sshserver.ssh_exec(add_tier)
            self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            # 创建测试文件
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1 oflag=direct" % path1)
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=100M count=1 oflag=direct" % path2)
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=500M count=1 oflag=direct" % path3)
            # 文件stat状态查看
            _, res = self.sshclient1.ssh_exec("stat " + path1)
            stat1_old = res.split("\n")[5:7]
            # _, stat2_old = self.sshclient1.ssh_exec("stat " + path2)
            # _, stat3_old = self.sshclient1.ssh_exec("stat " + path3)
            # 上传文件至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            sleep(60)
            # 同时下载所有文件
            from concurrent.futures import ThreadPoolExecutor, as_completed
            pools = []
            pool = ThreadPoolExecutor(max_workers=3)
            p1 = pool.submit(self.sshclient1.ssh_exec, "md5sum " + path1)
            p2 = pool.submit(self.sshclient1.ssh_exec, "echo fdsjgjj >> " + path2)
            p3 = pool.submit(self.sshclient1.ssh_exec, "rm -fr " + path3)
            pools.append(p1)
            pools.append(p2)
            pools.append(p3)
            for t in as_completed(pools):
                stat = t.result()[0]
                assert stat == 0, "md5sum download failed."
            # 查看文件stat属性
            _, res = self.sshclient1.ssh_exec("stat " + path1)
            stat1_new = res.split("\n")[5:7]
            # _, stat2_new = self.sshclient1.ssh_exec("stat " + path2)
            # _, stat3_new = self.sshclient1.ssh_exec("stat " + path3)
            assert stat1_old == stat1_new, "The attributes of the uploaded and downloaded files are inconsistent"
            # assert stat2_old == stat2_new, "The attributes of the uploaded and downloaded files are inconsistent"
        finally:
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))

    @pytest.mark.skipif(len(consts.CLIENT) < 2, reason="need two client")
    def test_twoclient_operation(self, get_data):
        """
        2447 不同客户端同时对一个目录的同一个文件进行操作，是否触发resyncing
        """
        tiering_id = "9006"
        path1 = self.testpath + "file1"
        client2 = consts.CLIENT[1]
        sshclient2 = sshClient(client2)
        try:
            # 创建测试文件
            self.sshserver.ssh_exec("mkdir -p " + self.testpath)
            # 添加分层
            add_tier = self.get_cli("mirror_add", self.testdir, self.bucketid, self.mirrorid, "1", "00:00", tiering_id)
            self.sshserver.ssh_exec(add_tier)
            self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, get_data))
            # 客户端挂载
            stat1 = client_mount(self.client1, acl_add=True)
            assert stat1 == 0, "client mount failed."
            stat2 = client_mount(client2, acl_add=True)
            assert stat2 == 0, "client mount failed."
            # 客户端写入数据
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=100M count=1 oflag=direct" % path1)
            # 上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", tiering_id))
            sleep(30)
            # 多个客户端操作同一文件
            from concurrent.futures import ThreadPoolExecutor, as_completed
            pools = []
            pool = ThreadPoolExecutor(max_workers=2)
            p1 = pool.submit(self.sshclient1.ssh_exec, "md5sum " + path1)
            p2 = pool.submit(sshclient2.ssh_exec, "rm -fr " + path1)
            pools.append(p1)
            pools.append(p2)
            as_completed(pools)
            # 判断集群正常无报错
            check_cluster_health(1)
        finally:
            sshclient2.close_connect()
            self.sshserver.ssh_exec("rm -fr " + self.testpath)
            self.sshserver.ssh_exec(self.get_cli('tiering_del', tiering_id))
