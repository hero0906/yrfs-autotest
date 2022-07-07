#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Desciption : s3 mirror case suite
@Time : 2022/01/14 17:00
@Author : caoyi
"""
import os
import pytest
import time
from time import sleep
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from common.client import client_mount
from common.s3cmd import S3Object
from common.s3depend import check_layer, check_recover_stat

yrfs_version = int(consts.YRFS_VERSION[:2])


@pytest.mark.skipif(yrfs_version <= 66, reason="only 66* verison need run.")
@pytest.mark.funcTest
class Tests3Mirror(YrfsCli):
    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.CLUSTER_VIP
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        # 测试目录定义
        self.tiering_id = "9060"
        self.testdir = "autotest_mirror_%s" % time.strftime("%m-%d-%H%M%S")
        self.mountdir = consts.MOUNT_DIR
        self.testpath = os.path.join(self.mountdir, self.testdir)
        self.fio = "fio -iodepth=16 -numjobs={} -bs=4K -ioengine=psync -group_report -name=autotest -size={} \
        -directory={} -nrfiles={} -direct=1"
        # 测试命令获取
        self.flush_cmd = self.get_cli(self, "tiering_flush")
        self.update_state = self.get_cli(self, "state_update")
        self.set_recover = self.get_cli(self, "set_recover")
        self.set_recover_full = self.set_recover + " --full"
        self.s3_recover_stat = self.get_cli(self, "s3_recover_stat")
        # 添加s3 mirror bucket
        add_bucket = self.get_cli(self, "bucket_add")
        self.del_bucket = self.get_cli(self, "bucket_del")
        self.sshserver.ssh_exec(self.del_bucket.format(consts.s3["bucketid"]))
        self.sshserver.ssh_exec(self.del_bucket.format(consts.s3["mirrorid"]))
        stat1, _ = self.sshserver.ssh_exec(add_bucket.format(consts.s3["hostname"], consts.s3["protocol"],
                                                             consts.s3["bucketname"], consts.s3["uri_style"],
                                                             consts.s3["region"], consts.s3["access_key"],
                                                             consts.s3["secret_access_key"], consts.s3["token"],
                                                             consts.s3["type"], consts.s3["bucketid"]))

        stat2, _ = self.sshserver.ssh_exec(add_bucket.format(consts.s3["hostname"], consts.s3["protocol"],
                                                             consts.s3["bucketmirror"], consts.s3["uri_style"],
                                                             consts.s3["region"], consts.s3["access_key"],
                                                             consts.s3["secret_access_key"], consts.s3["token"],
                                                             consts.s3["type"], consts.s3["mirrorid"]))
        if stat1 != 0 or stat2 != 0:
            pytest.skip(msg="add bucket failed, test skip", allow_module_level=True)
        # 添加分层、创建测试目录
        self.sshserver.ssh_exec("cd %s&&rm -fr autotest_mirror*&&mkdir -p %s" % (self.mountdir, self.testpath))
        self.sshserver.ssh_exec(self.get_cli(self, "tiering_del", self.tiering_id))
        add_tier = self.get_cli(self, "mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "1",
                                "00:00", self.tiering_id) + " --mode=1"
        stat, _ = self.sshserver.ssh_exec(add_tier)
        assert stat == 0, "add tiering failed."

    def teardown_class(self):
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.ssh_exec(self.get_cli(self, "tiering_del", self.tiering_id))
        self.sshserver.ssh_exec(self.del_bucket.format(consts.s3["bucketid"]))
        self.sshserver.ssh_exec(self.del_bucket.format(consts.s3["mirrorid"]))
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_mirror_3948(self):
        """
        3941 seek mode下批量上传100个1M小文件测试，检验数据是否落入local和public;3948 删除本地数据mirror bucket数据清空
        """
        try:
            mount = client_mount(self.clientip, acl_add=True)
            assert mount == 0, "client mount failed."
            # 写入数据
            self.sshclient.ssh_exec(self.fio.format("1", "100M", self.testpath, 10))
            # 查看刷入数据之前的s3容量
            local_s3object = S3Object(bucket=consts.s3["bucketname"])
            public_s3object = S3Object(bucket=consts.s3["bucketmirror"])
            local_keys_old = local_s3object.get_keys()
            public_keys_old = public_s3object.get_keys()
            # 刷入s3
            sleep(2)
            self.sshserver.ssh_exec(self.flush_cmd.format(self.tiering_id))
            sleep(30)
            for i in range(10):
                fname = self.testdir + "/autotest.0." + str(i)
                check_layer(fname, layer="S3", tierid=self.tiering_id)
            # 再次检查s3使用容量
            s3object = S3Object(bucket=consts.s3["bucketname"])
            local_keys_new = s3object.get_keys()
            s3object = S3Object(bucket=consts.s3["bucketmirror"])
            public_keys_new = s3object.get_keys()
            # 检验s3容量增加数量一致
            assert local_keys_new - local_keys_old == public_keys_new - public_keys_old, "S3 capacity is inconsistent"
            # mirror s3增加的容量相同
            assert local_keys_new > local_keys_old, "S3 capacity has not increased"
            # 文件删除后s3容量减少
            self.sshclient.ssh_exec("rm -fr %s/*" % self.testpath)
            sleep(30)
            local_keys_del = local_s3object.get_keys()
            public_keys_del = public_s3object.get_keys()
            assert local_keys_del < local_keys_new, "After s3 delete, the capacity is not reduced."
            # mirror s3释放的空间相同
            assert local_keys_new - local_keys_del == public_keys_new - public_keys_del, "S3 capacity is not released "
        finally:
            self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)

    def test_mirror_3959(self):
        """
        3959 mirror s3增量同步测试
        """
        subpath1 = self.testpath + "/dir1"
        subpath2 = self.testpath + "/dir2"
        try:
            self.sshserver.ssh_exec("mkdir -p %s %s" % (subpath1, subpath2))
            mount = client_mount(self.clientip, acl_add=True)
            assert mount == 0, "client mount failed."
            # 计算当前的s3基准容量
            local_bucket = S3Object(bucket=consts.s3["bucketname"])
            public_bucket = S3Object(bucket=consts.s3["bucketmirror"])
            local_keys_old = local_bucket.get_keys()
            public_keys_old = public_bucket.get_keys()
            # 创建第一批测试数据并记录md5值
            self.sshclient.ssh_exec(self.fio.format("1", "100M", subpath1, 10))
            _, md5sum_dir1_old = self.sshclient.ssh_exec("md5sum %s/*" % subpath1)
            # 上传第一批数据
            sleep(2)
            self.sshserver.ssh_exec(self.flush_cmd.format(self.tiering_id))
            sleep(60)
            # 设置localstate等于2
            stat, _ = self.sshserver.ssh_exec(self.update_state.format(self.tiering_id, 2))
            assert stat == 0, "set localstate=2 failed."
            # 再次创建第二批数据并记录md5值
            self.sshclient.ssh_exec(self.fio.format("1", "100M", subpath2, 10))
            _, md5sum_dir2_old = self.sshclient.ssh_exec("md5sum %s/*" % subpath2)
            # 上传第二批数据
            sleep(2)
            self.sshserver.ssh_exec(self.flush_cmd.format(self.tiering_id))
            sleep(60)
            # 设置localstate等于3
            stat, _ = self.sshserver.ssh_exec(self.update_state.format(self.tiering_id, 3))
            assert stat == 0, "set localstate=3 failed."
            # 执行增量同步操作
            sleep(1)
            stat, _ = self.sshserver.ssh_exec(self.set_recover.format(self.tiering_id))
            assert stat == 0, "Incremental sync failed."
            # 查看增量恢复完成进度
            sleep(10)
            for i in range(20):
                resync_info = check_recover_stat(self.tiering_id)
                resync_stat = resync_info["Resync_stat"]
                resync_type = resync_info["Resync_type"]
                if resync_stat == "Finished":
                    assert resync_type == "increase", "Not increase sync."
                    break
                else:
                    sleep(10)
            else:
                assert False, "increase sync failed."
            # 再次计算md5值
            _, md5sum_dir1_new = self.sshclient.ssh_exec("md5sum %s/*" % subpath1)
            _, md5sum_dir2_new = self.sshclient.ssh_exec("md5sum %s/*" % subpath2)
            assert md5sum_dir1_old == md5sum_dir1_new, "md5sum mismatch."
            assert md5sum_dir2_old == md5sum_dir2_new, "md5sum mismatch."
            # 查看两个bucket的数据新增容量一致
            local_keys_new = local_bucket.get_keys()
            public_keys_new = public_bucket.get_keys()
            assert local_keys_new - local_keys_old == public_keys_new - public_keys_old, \
                "local and public bucket keys inconsistent."
        finally:
            self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)

    def test_mirror_3960(self):
        """
        3960 mirror s3全量同步测试后数据md5sum一致
        """
        try:
            # 客户端挂载
            mount = client_mount(self.clientip, acl_add=True)
            assert mount == 0, "client mount failed."
            # 创建测试文件并记录md5sum
            self.sshclient.ssh_exec(self.fio.format("4", "100M", self.testpath, 5))
            _, md5sum_old = self.sshclient.ssh_exec("md5sum %s/*" % self.testpath)
            # 上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.flush_cmd.format(self.tiering_id))
            sleep(60)
            # 查看s3容量
            local_bucket = S3Object(bucket=consts.s3["bucketname"])
            public_bucket = S3Object(bucket=consts.s3["bucketmirror"])
            local_keys_old = local_bucket.get_keys()
            public_keys_old = public_bucket.get_keys()
            # 执行全量恢复，查看恢复进度
            stat, _ = self.sshserver.ssh_exec(self.set_recover_full.format(self.tiering_id))
            assert stat == 0, "full recover failed."
            for i in range(20):
                resync_info = check_recover_stat(self.tiering_id)
                resync_stat = resync_info["Resync_stat"]
                resync_type = resync_info["Resync_type"]
                if resync_stat == "Finished":
                    assert resync_type == "full", "Not full sync."
                    break
                else:
                    sleep(10)
            else:
                assert False, "full sync failed."
            # 再次检测s3容量，对比之前未发生变化
            local_keys_new = local_bucket.get_keys()
            public_keys_new = public_bucket.get_keys()
            assert local_keys_old == local_keys_new, "full sync local s3 capacity is inconsistent"
            assert public_keys_old == public_keys_new, "full sync public s3 capacity is inconsistent"
        finally:
            self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)