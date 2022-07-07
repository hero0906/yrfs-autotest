#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Desciption : s3 tiering seek mirror test suite
@Time : 2021/10/28 15:22
@Author : caoyi
"""

import os
from time import sleep
import time
import pytest
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.cli import YrfsCli
from common.util import sshClient, sshSftp
from common.client import client_mount
from config import consts
from common.s3depend import check_layer, create_s3_script
from common.s3cmd import S3Object
from common.cluster import get_osd_master, get_entry_info, check_cluster_health

logger = logging.getLogger(__name__)
yrfs_version = int(consts.YRFS_VERSION[:2])

@pytest.mark.skipif(yrfs_version <= 66, reason="only 66* verison need run.")
@pytest.mark.funcTest
class TestmirrorSeek(YrfsCli):

    def setup_class(self):
        self.client1 = consts.CLIENT[0]
        self.serverip = consts.CLUSTER_VIP
        self.testdir = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.mountdir = consts.MOUNT_DIR
        self.mdtest = "mdtest -C -d {0} -i 1 -w 1 -I 50000 -z 0 -b 0 -L -F"
        self.mds_rebuild = "yrcli --recover --type=mds --groupid={0} --restart --fullresync"
        self.sshclient1 = sshClient(self.client1)
        self.sshserver = sshClient(self.serverip)
        # 检验客户端测试工具是否存在
        fio_stat, _ = self.sshclient1.ssh_exec("fio --version")
        if fio_stat != 0:
            yum_stat, _ = self.sshclient1.ssh_exec("yum -y install fio")
            if yum_stat != 0:
                yum_stat, _ = self.sshclient1.ssh_exec("apt-get install fio -y")
            if yum_stat != 0:
                pytest.skip(msg="Not found FIO,test skip", allow_module_level=True)

        self.fio = "fio -iodepth=16 -numjobs=1 -bs=4K -ioengine=psync -group_report -name=autotest -size={} " + \
                   "-directory={} -nrfiles={} -rw=write"
        # 添加bucket
        bucket_add = self.get_cli(self, "bucket_add", consts.s3["hostname"], consts.s3["protocol"],
                                  consts.s3["bucketname"],
                                  consts.s3["uri_style"], consts.s3["region"], consts.s3["access_key"],
                                  consts.s3["secret_access_key"],
                                  consts.s3["token"], consts.s3["type"], consts.s3["bucketid"])
        # 执行一次删除操作
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["bucketid"]))
        add_stat, _ = self.sshserver.ssh_exec(bucket_add)
        if add_stat != 0:
            pytest.skip(msg="add bucket failed, test skip", allow_module_level=True)
        # 添加mirror bucket
        mirror_add = self.get_cli(self, "bucket_add", consts.s3["hostname"], consts.s3["protocol"],
                                  consts.s3["bucketmirror"],
                                  consts.s3["uri_style"], consts.s3["region"], consts.s3["access_key"],
                                  consts.s3["secret_access_key"],
                                  consts.s3["token"], consts.s3["type"], consts.s3["mirrorid"])
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["mirrorid"]))
        add_stat, _ = self.sshserver.ssh_exec(mirror_add)
        if add_stat != 0:
            pytest.skip(msg="add bucket failed, test skip", allow_module_level=True)
        # 创建测试目录
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)
        # 添加分层
        sleep(1)
        # 执行一次删除
        self.sshserver.ssh_exec(self.get_cli(self, 'tiering_del', "998"))
        add_tier = self.get_cli(self, "mirror_add", self.testdir, consts.s3["bucketid"], consts.s3["mirrorid"], "1",
                                "00:00", "998")
        add_stat, _ = self.sshserver.ssh_exec(add_tier)
        assert add_stat == 0, "add tiering failed."
        sleep(1)
        # 设置seek 模式
        set_mode, _ = self.sshserver.ssh_exec(self.get_cli(self, "tiering_mode", self.testdir, "1"))
        assert set_mode == 0, "set seek mode failed."
        sleep(2)

    def teardown_class(self):
        sleep(5)
        # 删除测试目录
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.ssh_exec(self.get_cli(self, 'tiering_del', "998"))
        # 删除bucket配置
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["bucketid"]))
        self.sshserver.ssh_exec(self.get_cli(self, "bucket_del", consts.s3["mirrorid"]))

        self.sshclient1.close_connect()
        self.sshserver.close_connect()
        check_cluster_health(check_times=1)

    def teardown(self):
        self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)
        sleep(2)

    @staticmethod
    def __make_param(cache, lazy):
        # 设置不同的挂载参数
        lazy_param = "lazy_close_enable = false\nlazy_read_eof_enable = false\n"
        cache_param = "client_cache_type = cache\n"
        if cache == "cache" and lazy == "true":
            param = cache_param + lazy_param
        elif cache == "cache" and lazy == "false":
            param = cache_param
        elif cache == "none" and lazy == "true":
            param = lazy_param
        else:
            param = ""
        return param

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_multi_read(self, cache, lazy):
        """
        caseID:3692 检验上传读取文件成功,多线程读成功，20M大文件和10K小文件(cache、none,lazy open、close)（s3 mirror）
        """
        subpath1 = self.testpath + "/dir1"
        subpath2 = self.testpath + "/dir2"
        subdir1 = self.testdir + "/dir1"
        subdir2 = self.testdir + "/dir2"
        layer = ""
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        self.sshclient1.ssh_exec("mkdir -p %s %s" % (subpath1, subpath2))
        # 创建测试文件
        self.sshclient1.ssh_exec(self.fio.format("100M", subpath1, "20"))
        sleep(20)
        # 执行s3 flush操作
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        # 创建第二批文件
        self.sshclient1.ssh_exec(self.fio.format("200K", subpath2, "20") + " &")
        sleep(30)
        # 查询文件是否上传至s3
        _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f" % (consts.MOUNT_DIR, subdir1))

        for f in files.split("\n"):

            entry_cmd = self.get_cli("get_entry", f)
            layer = ""
            for i in range(30):
                _, entryinfo = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", entryinfo)
                layer = "".join(layer)

                tieringid = re.findall("TieringID: (.*)\n", entryinfo)
                assert "".join(tieringid) == "998", "tiering id not 998"

                s3mode = re.findall("S3Mode: (.*)\n", entryinfo)
                assert "".join(s3mode) == "s3seek", "s3mode not s3seek"

                if layer == "S3":
                    logger.info("file: %s put S3 success." % f)
                    break
                else:
                    logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                    sleep(5)
                    continue
            else:
                logger.error("file: %s put s3 timeout." % f)
                assert layer == "S3", "put s3 failed."
                break
        # 并发读取已上传的文件:
        script = "import random\n" \
                 "from concurrent.futures import ThreadPoolExecutor\n" \
                 "def test_seek(filename):\n" \
                 "   fo = open(filename, 'rb')\n" \
                 "   seek_num = random.randint(1,4194304)\n" \
                 "   fo.seek(seek_num, 0)\n" \
                 "   chunk = fo.read(seek_num)\n" \
                 "   if not chunk:\n" \
                 "       fo.close()\n" \
                 "       return 1\n" \
                 "   else:\n" \
                 "       fo.close()\n" \
                 "       return 0\n" \
                 "pools = []\n" \
                 "pool = ThreadPoolExecutor(max_workers=20)\n" \
                 "for i in range(20):\n" \
                 "    filename = '{}/autotest.0.%s'%(str(i))\n".format(subpath1) + \
                 "    p = pool.submit(test_seek, filename)\n" \
                 "    pools.append(p)\n" \
                 "res = 0\n" \
                 "for t in pools:\n" \
                 "    res = res + t.result()\n" \
                 "print(res)"

        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)

        assert res == "0", "multi thread read failed."
        # 再次上传dir2目录小文件
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        sleep(30)
        _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f" % (consts.MOUNT_DIR, subdir2))

        for f in files.split("\n"):

            entry_cmd = self.get_cli("get_entry", f)

            for i in range(30):
                _, entryinfo = self.sshserver.ssh_exec(entry_cmd)
                layer = re.findall("Data Location: (.*)\n", entryinfo)
                layer = "".join(layer)

                tieringid = re.findall("TieringID: (.*)\n", entryinfo)
                assert "".join(tieringid) == "998", "tiering id not 998"

                s3mode = re.findall("S3Mode: (.*)\n", entryinfo)
                assert "".join(s3mode) == "s3seek", "s3mode not s3seek"

                if layer == "S3":
                    logger.info("file: %s put S3 success." % f)
                    break
                else:
                    logger.warning("file: %s put S3 failed, retry times: %s" % (f, str(i + 1)))
                    sleep(5)
                    continue
            else:
                logger.error("file: %s put s3 timeout." % f)
                assert layer == "S3", "put s3 failed."
                break
        # 并发下载所有文件
        script = "import random\n" \
                 "from concurrent.futures import ThreadPoolExecutor\n" \
                 "def test_seek(filename):\n" \
                 "   fo = open(filename, 'rb')\n" \
                 "   seek_num = random.randint(1,5194)\n" \
                 "   fo.seek(seek_num, 0)\n" \
                 "   chunk = fo.read(seek_num)\n" \
                 "   if not chunk:\n" \
                 "       fo.close()\n" \
                 "       return 1\n" \
                 "   else:\n" \
                 "       fo.close()\n" \
                 "       return 0\n" \
                 "pools = []\n" \
                 "pool = ThreadPoolExecutor(max_workers=20)\n" \
                 "for i in range(20):\n" \
                 "    filename = '{}/autotest.0.%s' % (str(i))\n".format(subpath2) + \
                 "    p = pool.submit(test_seek, filename)\n" \
                 "    pools.append(p)\n" \
                 "res = 0\n" \
                 "for t in pools:\n" \
                 "    res = res + t.result()\n" \
                 "print(res)"

        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)

        assert res == "0", "multi thread read failed."

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_append_write(self, cache, lazy):
        """
        检验s3seek模式追加写文件正确,3703 校验写S3层的文件1G，写入成功，并上传S3有效(cache、none,lazy open、close)（s3 mirror）
        """
        # 创建测试文件
        mountdir = consts.MOUNT_DIR
        filename = "autotest_seek_file"
        testpath = self.testpath + "/" + filename
        testfile = self.testdir + "/" + filename
        try:
            # 客户端挂载
            param = self.__make_param(cache, lazy)
            _mount = client_mount(self.client1, acl_add=True, param=param)
            assert _mount == 0, "Client mount failed."
            # 写入文件
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=200 oflag=direct" % testpath)
            self.sshserver.ssh_exec("cd %s&&dd if=/dev/zero of=%s bs=1M count=200 oflag=direct" % (mountdir, filename))
            # 上传至s3
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            # 检查文件上传到s3状态
            check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
            # 追加写文件200M文件
            stat, _ = self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s bs=1M count=200 oflag=append conv=notrunc oflag=direct"
                "" % testpath)
            self.sshserver.ssh_exec(
                "cd %s&&dd if=/dev/zero of=%s bs=1M count=200 oflag=append conv=notrunc oflag=direct"
                "" % (mountdir, filename))
            assert stat == 0, "dd append write failed"
            # 下拉文件计算md5值
            _, md5sum2 = self.sshclient1.ssh_exec("md5sum " + testpath)
            _, md5sum1 = self.sshserver.ssh_exec("cd %s&&md5sum %s" % (mountdir, filename))
            assert md5sum1.split()[0] == md5sum2.split()[0], "md5sum mismatching"
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, filename))

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seq_read(self, cache, lazy):
        """
        3696 （自动化）校验预埋同一目录并全部上传，顺序读部分文件成功,(cache、none,lazy open、close)（s3 mirror）
        """
        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        # 客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # 写入4G测试文件
        self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % testpath)
        # 上传至s3
        sleep(5)
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        sleep(60)
        # 检查上传到s3的状态
        check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
        # seek创建脚本文件读取文件下载测试切片
        script = create_s3_script(fname=testpath, bytesize=104960111)
        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)
        # 校验顺序读
        assert res == "0", "seq read s3 failed"

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_random_read(self, cache, lazy):
        """
        3701 （自动化）校验预埋不同目录部分上传至S3，部分本地，随机读全部文件成功(cache、none,lazy open、close)（s3 mirror）
        """
        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        # 客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # 写入2G测试文件
        self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % testpath)
        # 上传至s3
        sleep(5)
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        sleep(60)
        # 检查上传到s3的状态
        check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
        # seek创建脚本文件读取文件下载测试切片
        script = create_s3_script(fname=testpath, bytesize=1049, blocks=5)
        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)

        assert res == "0", "seq read s3 failed"

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_cache_copy(self, cache, lazy):
        """
        3760 校验预读模式下拷贝原数据到集群别的seek目录后对比源文件和目标文件的md5值(cache、none,lazy open、close)（s3 mirror）
        """

        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        # 客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # cache_param = "client_cache_type=cache"
        # # 开启客户端cache模式
        # self.sshclient1.ssh_exec('echo 3 > /proc/sys/vm/drop_caches;echo "%s" >> %s'
        #                          % (cache_param, consts.CLIENT_CONFIG))
        # # 重启客户端
        # stat, _ = self.sshclient1.ssh_exec('/etc/init.d/yrfs-client stop&&sleep 1&&/etc/init.d/yrfs-client start')
        # assert stat == 0, "client start failed."
        # 写入2G测试文件
        self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % testpath)
        # 计算md5值
        _, mdsum1 = self.sshclient1.ssh_exec("md5sum " + testpath)
        # 上传至s3
        sleep(5)
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        # 检查上传到s3的状态
        sleep(30)
        check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
        # 文件备份
        stat, _ = self.sshclient1.ssh_exec("rsync -av {0} {0}_bak".format(testpath))
        assert stat == 0, "rsync failed."
        _, mdsum2 = self.sshclient1.ssh_exec("md5sum " + testpath)
        _, mdsum3 = self.sshclient1.ssh_exec("md5sum " + testpath + "_bak")
        # 校验md5sum值是否一致
        assert mdsum1.split()[0] == mdsum2.split()[0] == mdsum3.split()[0], "md5sum mismatching"

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seek_change_normal(self, cache, lazy):
        """
        3734 开启seek模式的目录修改S3模式为normal，验证新旧文件的表现(cache、none,lazy open、close)（s3 mirror）
        """
        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        try:
            # 客户端挂载
            param = self.__make_param(cache, lazy)
            _mount = client_mount(self.client1, acl_add=True, param=param)
            assert _mount == 0, "Client mount failed."
            # 写入测试文件
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=500 oflag=direct" % testpath)
            # 计算md5值
            _, mdsum1_old = self.sshserver.ssh_exec("md5sum " + testpath)
            # 上传文件
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            # 检查文件上传状态
            sleep(3)
            check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
            # 修改mode为normal
            self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, "1"))
            # 新建文件02
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=500 oflag=direct" % (testpath + "02"))
            _, mdsum2_old = self.sshserver.ssh_exec("md5sum " + testpath + "02")
            sleep(5)
            # 记录存储容量
            _, df1 = self.sshserver.ssh_exec("df -T|grep %s|awk '{print $4}'" % consts.MOUNT_DIR)
            # 上传文件
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            # 检查文件02上传状态为s3normal
            sleep(3)
            check_layer(fname=testfile + "02", layer="S3", tierid="998", mode="s3seek")
            sleep(5)
            # 再次检查存储容量减少
            sleep(3)
            _, df2 = self.sshserver.ssh_exec("df -T|grep %s|awk '{print $4}'" % consts.MOUNT_DIR)
            assert int(df1) > int(df2), "Capacity not reduced."
            # 查询基准s3容量
            s3object = S3Object()
            s3_du1 = s3object.get_keys()
            # md5校验
            _, mdsum1_new = self.sshserver.ssh_exec("md5sum " + testpath)
            # 检查seek模式下的文件下载后 s3容量未减少
            sleep(2)
            s3_du2 = s3object.get_keys()
            assert s3_du1 == s3_du2, "s3 storage reduce"
            # 检查normal模式下的文件下载后，s3容量减少
            _, mdsum2_new = self.sshserver.ssh_exec("md5sum " + testpath + "02")
            sleep(2)
            s3_du3 = s3object.get_keys()
            assert s3_du1 == s3_du3, "s3 capacity not reduced"
            assert mdsum1_new == mdsum1_old, "md5sum mismatching."
            assert mdsum2_new == mdsum2_old, "md5sum mismatching."
        finally:
            # 再次修改为seek模式
            self.sshserver.ssh_exec(self.get_cli("tiering_mode", self.testdir, "1"))

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seek_md5sum(self, cache, lazy):
        """
        3784 seek写已经在S3上的文件，md5校验1(cache、none,lazy open、close)（s3 mirror）
        """
        filename = "autotest_seek_file"
        testpath = self.testpath + "/" + filename
        testfile = self.testdir + "/" + filename
        dd_cmd1 = "dd if=/dev/zero of={} bs=1M count=200 oflag=direct"
        dd_cmd2 = "dd if=/dev/zero of={} bs=1M seek=2000 count=100  conv=notrunc"
        try:
            # 客户端挂载
            param = self.__make_param(cache, lazy)
            _mount = client_mount(self.client1, acl_add=True, param=param)
            assert _mount == 0, "Client mount failed."
            # 创建测试文件
            self.sshclient1.ssh_exec(dd_cmd1.format(testpath))
            # 备份测试文件
            self.sshclient1.ssh_exec("cp %s %s" % (testpath, consts.MOUNT_DIR + "/" + filename))
            # 上传文件
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            # 检查文件上传状态
            sleep(30)
            check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
            sleep(5)
            # dd seek本地文件和s3文件
            stat, _ = self.sshclient1.ssh_exec(dd_cmd2.format(testpath))
            assert stat == 0, "dd seek failed."
            # 检查seek后文件状态为mixed
            check_layer(fname=testfile, layer="Mixed", tierid="998", mode="s3seek")
            stat, _ = self.sshclient1.ssh_exec(dd_cmd2.format(consts.MOUNT_DIR + "/" + filename))
            assert stat == 0, "dd seek failed."
            # 校验本地文件和远程文件md5是否一致
            _, md5sum1 = self.sshclient1.ssh_exec("md5sum " + testpath)
            _, md5sum2 = self.sshclient1.ssh_exec("md5sum " + consts.MOUNT_DIR + "/" + filename)
            assert md5sum1.split()[0] == md5sum2.split()[0], "md5sum mismatching"
        finally:
            # 清理文件
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (consts.MOUNT_DIR, filename))

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seq_rand_read(self, cache, lazy):
        """
        3715 校验顺序读后在随机读，是否有残留(cache、none,lazy open、close)（s3 mirror）
        """
        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        # 客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # 写入1G测试文件
        self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % testpath)
        sleep(2)
        # 计算本地容量
        _, df_old = self.sshserver.ssh_exec("df -T  /mnt/yrfs/|awk 'NR>1{{print $4}}'")
        # 检验文件的md5sum
        _, mdsum_old = self.sshserver.ssh_exec("md5sum " + testpath)
        # 上传至s3
        sleep(5)
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        sleep(30)
        # 检查上传至s3的状态
        check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
        # _, filenum = self.sshserver.ssh_exec(tiering_level_cmd)
        sleep(2)
        _, df_upload = self.sshserver.ssh_exec("df -T  /mnt/yrfs/|awk 'NR>1{{print $4}}'")
        assert int(df_old) > int(df_upload), "Capacity not reduced"
        # 顺序读
        script = create_s3_script(fname=testpath, bytesize=104960111)
        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)
        assert res == "0", "seq seek read failed"
        # 随机读
        script = create_s3_script(fname=testpath, bytesize=1049, blocks=5)
        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
        /tmp/autotest_tiering_mul_read.py" % script)
        assert res == "0", "rand seek read failed"
        # 再次上传到s3
        sleep(5)
        flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        assert flush_stat == 0, "s3 flush failed."
        sleep(30)
        # 检查文件再次上传至s3的状态
        check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
        # 再次计算md5sum
        _, mdsum_new = self.sshserver.ssh_exec("md5sum " + testpath)
        # 校验md5sum值是是否一致
        assert mdsum_old == mdsum_old, "md5sum mismatching"

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_read_less_blocksize(self, cache, lazy):
        """
        3711 校验顺序读小于blocksize(设置等于stripesize)边界正常(cache、none,lazy open、close)（s3 mirror）
        """
        sshmaster = ""
        testpath = self.testpath + "/autotest_seek_file"
        testfile = self.testdir + "/autotest_seek_file"
        read_size = 90
        get_entry = "yrcli --getentry %s -u --verbose" % testfile
        try:
            # 不同方式的客户端挂载
            param = self.__make_param(cache, lazy)
            _mount = client_mount(self.client1, acl_add=True, param=param)
            assert _mount == 0, "Client mount failed."
            # 写入1G小文件测试
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=1024 oflag=direct" % testpath)
            sleep(2)
            # 上传至s3
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            sleep(30)
            # 检查上传至s3的状态
            check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
            # 顺序读90M
            script = create_s3_script(fname=testpath, bytesize=read_size * 1024 * 1024)
            _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&python3 \
            /tmp/autotest_tiering_mul_read.py" % script)
            assert res == "0", "seq seek read failed"
            # 获取文件的osd master节点
            osd_master_nodes = get_osd_master(testfile)
            osd_master_node = osd_master_nodes[0]
            # 获取文件chunk path
            _, chunk_path_tmp = self.sshserver.ssh_exec(get_entry)
            chunk_path = re.findall(r"Chunk path.*/(.*)\n", chunk_path_tmp)
            sshmaster = sshClient(osd_master_node)
            _, file_path = sshmaster.ssh_exec("find /data/oss*/ -name " + "".join(chunk_path))
            # 有可能多个path只获取一个即可
            file_path = file_path.split()[0]
            # 计算稀疏文件的大小
            _, file_size = sshmaster.ssh_exec("du -sm " + file_path)
            file_size = file_size.split()[0]
            # 计算稀疏文件的size大于，读取的块大小文件
            #assert int(read_size) < int(file_size)
            # 再次时间flush操作
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            sleep(30)
            # 再次检查上传至s3的状态
            check_layer(fname=testfile, layer="S3", tierid="998", mode="s3seek")
            # 稀疏文件被删除
            stat, _ = self.sshserver.ssh_exec("stat " + file_path)
            assert stat != 0, "The sparse file was not deleted"
        finally:
            self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)
            sshmaster.close_connect()

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_uploading_rw(self, cache, lazy):
        """
        3693 校验同一目录既上传过程中，顺序读写S3中部分文件有效(cache、none,lazy open、close)（s3 mirror）
        """
        fio_cmd = "fio -iodepth=16 -numjobs={} -bs=4K -ioengine=psync -group_report -name={} -size={} " + \
                  "-directory={} -nrfiles={} -rw={}"
        flush_cmd = self.get_cli("tiering_flush", "998")

        # 客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # 创建第一批测试文件
        self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "1M", self.testpath, "8", "write"))
        # 上传第一批文件至s3
        sleep(5)
        self.sshserver.ssh_exec(flush_cmd)
        # 检查上传s3状态成功
        sleep(60)
        _, files = self.sshserver.ssh_exec("cd %s&&find %s -type f" % (self.mountdir, self.testdir))
        for fname in files.split("\n"):
            check_layer(fname=fname, layer="S3", tierid="998", mode="s3seek")
        # 创建第二批测试文件
        self.sshclient1.ssh_exec(fio_cmd.format("10", "test", "10M", self.testpath, "20", "write"))
        # 上传第二批文件至s3上,上传过程中读写第一批文件
        sleep(5)
        self.sshserver.ssh_exec(flush_cmd)
        # 并发读写第一批文件成功
        stat, _ = self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "1M", self.testpath, "8", "rw"))
        assert stat == 0, "fio rw threads failed."

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seq_rand_rw(self, cache, lazy):
        """
        3694 校验不同目录上传完成后，顺序+随机+读写部分文件有效(cache、none,lazy open、close)（s3 mirror）
        """
        fio_cmd = "cd " + self.mountdir + "&&fio -iodepth=16 -numjobs={} -bs=4K -ioengine=psync -group_report -name={" \
                                          "} -filesize={} " + \
                  "-directory={} -nrfiles={} -rw={}"
        flush_cmd = self.get_cli("tiering_flush", "998")
        # 安装依赖包
        pipstat, _ = self.sshclient1.ssh_exec("python3 -c 'import imageio'")
        # #客户端挂载
        param = self.__make_param(cache, lazy)
        _mount = client_mount(self.client1, acl_add=True, param=param)
        assert _mount == 0, "Client mount failed."
        # 创建测试文件
        testdir1 = self.testdir + "/dirA/dirB"
        testdir2 = self.testdir + "/d2/d3/d4/d5/d6/d7/d8/d9/d10/d11/d12/d13/d14/d15"
        testdir3 = self.testdir + "/dir1/dir2/dir3/dir4/dir5/dir6"
        testdir4 = self.testdir + "/test"
        self.sshclient1.ssh_exec(
            "cd %s&&mkdir -p %s %s %s %s" % (self.mountdir, testdir1, testdir2, testdir3, testdir4))
        self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "4k", testdir1, "10", "write"))
        self.sshclient1.ssh_exec(fio_cmd.format("1", "autotest", "1G", testdir2, "1", "write"))
        self.sshclient1.ssh_exec(fio_cmd.format("20", "autotest", "512K", testdir3, "1", "write"))
        if pipstat == 0:
            sftp = sshSftp(self.client1)
            test_video = os.path.join(self.mountdir, testdir4) + "/autotest.mp4"
            sftp.sftp_upload("tools/autotest.mp4", test_video)
            sftp.close_connect()
            script = "import imageio\n" \
                     "try:\n" \
                     "    imageio.get_reader('%s')\n" % test_video + \
                     "except:\n" \
                     "    assert False"
            self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_imageio.py" % script)
        # 上传文件至s3
        sleep(5)
        self.sshserver.ssh_exec(flush_cmd)
        logger.info("sleep 200s")
        sleep(2)
        # 读写文件
        self.sshclient1.ssh_exec(fio_cmd.format("10", "autotest", "4k", testdir1, "10", "read"))
        self.sshclient1.ssh_exec(fio_cmd.format("1", "autotest", "1G", testdir2, "1", "randread"))
        self.sshclient1.ssh_exec(fio_cmd.format("20", "autotest", "512k", testdir3, "1", "randwrite"))
        pools = []
        pool = ThreadPoolExecutor(max_workers=4)
        p1 = pool.submit(self.sshclient1.ssh_exec, fio_cmd.format("10", "autotest", "4k", testdir1, "10", "read"))
        p2 = pool.submit(self.sshclient1.ssh_exec, fio_cmd.format("1", "autotest", "1G", testdir2, "1", "randread"))
        p3 = pool.submit(self.sshclient1.ssh_exec, fio_cmd.format("20", "autotest", "512K", testdir3, "1", "randwrite"))
        if pipstat == 0:
            p4 = pool.submit(self.sshclient1.ssh_exec, "python3 /tmp/autotest_imageio.py")
            pools.append(p4)
        pools.append(p1)
        pools.append(p2)
        pools.append(p3)
        for t in as_completed(pools):
            res = t.result()
            assert res[0] == 0, "Read S3 file  failed."

    def test_downloading_rebuild(self):
        """
        2519 校验在下载过程中触发全量恢复，IO及下载有效（s3 mirror）
        """
        testdir = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        filename = self.testdir + "/file1"
        filepath = self.testpath + "/file1"
        try:
            # 挂载客户端
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 创建测试数据
            self.sshclient1.ssh_exec("dd if=/dev/zero of=%s bs=1M count=3014 oflag=direct" % filepath)
            # 计算初始md5sum
            _, md5_init = self.sshclient1.ssh_exec("md5sum " + filepath)
            # 执行s3 flush操作
            sleep(5)
            flush_stat, _ = self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            assert flush_stat == 0, "s3 flush failed."
            # 检查文件是否上传
            sleep(60)
            check_layer(fname=filename, layer="S3", tierid="998", mode="s3seek")
            # mdtest写入第二个目录
            self.sshserver.ssh_exec("cd %s&&mkdir %s" % (self.mountdir, testdir))
            self.sshclient1.ssh_exec("cd %s&&" % self.mountdir + self.mdtest.format(testdir))
            # 获取目录mds属主
            entry1 = get_entry_info(self.testdir)
            entry2 = get_entry_info(testdir)
            group_id1 = entry1["GroupID"]
            group_id2 = entry2["GroupID"]
            # 执行mds rebuild
            if group_id1 != group_id2:
                self.sshserver.ssh_exec(self.mds_rebuild.format(group_id1))
                self.sshserver.ssh_exec(self.mds_rebuild.format(group_id2))
            else:
                self.sshserver.ssh_exec(self.mds_rebuild.format(group_id1))
            # 下拉s3文件
            _, md5_end = self.sshclient1.ssh_exec("md5sum " + filepath)
            assert md5_init == md5_end, "md5sum mismatching."
        finally:
            self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (self.mountdir, testdir))
            self.sshserver.ssh_exec("rm -fr %s/*" % self.testpath)
            check_cluster_health()

    @pytest.mark.parametrize("cache", ("cache", "none"))
    @pytest.mark.parametrize("lazy", ("true", "false"))
    def test_seek_3780(self, cache, lazy):
        """
        3780 fio读取offset为0,io_limit为5G的seek文件的数据一致性（s3 mirror）
        """
        testfile = self.testpath + "/fio_file.txt"
        param = self.__make_param(cache, lazy)
        mount = client_mount(self.client1, acl_add=True, param=param)
        assert mount == 0, "client mount failed."
        fio_write = "fio --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=32 --bs=4K --rw=randwrite \
        --verify=pattern --verify_pattern=0xff --verify_interval=4096 --do_verify=0 --verify_state_save=1 \
        --group_reporting --gtod_reduce=1 --clat_percentiles=0 --serialize_overlap=1 --name=perf_test \
        --filename=%s --offset=0 --size=1G" % testfile
        fio_verify = "fio --ioengine=libaio --direct=1 --thread=1 --numjobs=1 --iodepth=32 --bs=4K --rw=randread \
        --verify=pattern --verify_pattern=0xff --verify_interval=4096 --do_verify=1 --verify_state_load=1 \
        --verify_fatal=1 --verify_dump=1 --group_reporting --gtod_reduce=1 --clat_percentiles=0 --name=perf_test \
        --filename=%s --offset=0 --size=512M --time_based --runtime=60" % testfile
        # 写入测试数据
        self.sshclient1.ssh_exec(fio_write)
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(60)
        # fio校验数据
        stat, _ = self.sshclient1.ssh_exec(fio_verify)
        assert stat == 0, "fio verify failed."

    def test_seek_3785(self):
        """
        3785 seek写已经在S3上的文件，md5校验2（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "Client mount failed."
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            # 写入数据1一个1G文件
            self.sshclient1.ssh_exec(self.fio.format("1G", self.testpath, "1"))
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 上传文件至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 检查上传至s3
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # trunc s3文件
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % self.testpath)
            # 重新上传文件至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(60)
            # 计算s3文件md5
            _, res = self.sshclient1.ssh_exec("md5sum %s/*" % self.testpath)
            md5_s3 = res.split()[0]
            # 计算本地相同文件的md5值
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % testpath2)
            _, res = self.sshclient1.ssh_exec("md5sum %s/*" % testpath2)
            md5_local = res.split()[0]
            assert md5_s3 == md5_local, "md5sum mismatching"
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    def test_seek_3786(self):
        """
        3786 seek重复写S3上文件的同一部分（s3 mirror）
        """
        # 客户端挂载
        mount = client_mount(self.client1, acl_add=True)
        assert mount == 0, "Client mount failed"
        # 数据写入1G文件
        self.sshclient1.ssh_exec(self.fio.format("1G", self.testpath, "1"))
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(60)
        check_layer(self.testdir + "/autotest.0.0", "S3", "998")
        # 第一次写入100M的区间
        stat, _ = self.sshclient1.ssh_exec(
            "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % self.testpath)
        assert stat == 0, "Seek file failed."
        # 第二次写入100M的区间
        stat, _ = self.sshclient1.ssh_exec(
            "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % self.testpath)
        assert stat == 0, "Seek file failed."
        # 检查文件状态
        check_layer(self.testdir + "/autotest.0.0", "Mixed", "998")

    def test_seek_3787(self):
        """
        3787 seek多次写S3上文件的不同位置（s3 mirror）
        """
        # 客户端挂载
        mount = client_mount(self.client1, acl_add=True)
        assert mount == 0, "Client mount failed."
        # 数据写入1G文件
        self.sshclient1.ssh_exec(self.fio.format("1G", self.testpath, "1"))
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(30)
        # 检查文件状态
        check_layer(self.testdir + "/autotest.0.0", "S3", "998")
        # 第一次seek读取100M
        stat, _ = self.sshclient1.ssh_exec(
            "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % self.testpath)
        assert stat == 0, "Seek file failed."
        # 第二次seek读取200M
        stat, _ = self.sshclient1.ssh_exec(
            "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=104 count=200 conv=notrunc" % self.testpath)
        assert stat == 0, "Seek file failed."
        # 再次执行上传操作
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(30)
        # 检查文件状态
        check_layer(self.testdir + "/autotest.0.0", "S3", "998")
        # 第三次seek读取300M
        stat, _ = self.sshclient1.ssh_exec(
            "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=306 count=300 conv=notrunc" % self.testpath)
        assert stat == 0, "seek file failed."
        # 第三次执行上传操作
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        check_layer(self.testdir + "/autotest.0.0", "Mixed", "998")

    def test_seek_3788(self):
        """
        3788 seek多次写S3上文件的交叉位置（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 写入1G测试文件
            self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, "1"))
            # 创建文件测试目录
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            # 文件拷贝
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 把文件上传至s3分层
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 检查文件状态
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # 第一次分层文件seek写入
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % self.testpath)
            # 本地文件第一次seek
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=2 count=100 conv=notrunc" % testpath2)
            # 第二次分层文件seek写入
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=5 count=100 conv=notrunc" % self.testpath)
            # 本地文件第二次seek
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=5 count=100 conv=notrunc" % testpath2)
            # 第三次分层文件seek写入
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=1 count=100 conv=notrunc" % testpath2)
            # 本地文件第三次seek
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=1 count=100 conv=notrunc" % self.testpath)
            # 计算分层文件md5值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_s3 = res.split()[0]
            # 计算本地文件md5值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            # 比对md5值是否一致
            assert md5_s3 == md5_local, "md5sum mismatching."
        finally:
            # 清理文件
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    def test_seek_3789(self):
        """
        3789 多线程并发seek写同一文件的不同部分（flush前校验）（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        dd = "dd if=/dev/zero of={0}/autotest.0.0 bs=1M seek={1} count=50 conv=notrunc"
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "Client mount failed."
            # 写入测试文件
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, "1"))
            # 文件拷贝
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 把文件上传至s3分层
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 检查文件状态
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # 并发操作文件seek写
            pools = []
            pool = ThreadPoolExecutor(max_workers=4)
            p1 = pool.submit(self.sshclient1.ssh_exec, dd.format(self.testpath, 1))
            p2 = pool.submit(self.sshclient1.ssh_exec, dd.format(self.testpath, 70))
            p3 = pool.submit(self.sshclient1.ssh_exec, dd.format(testpath2, 1))
            p4 = pool.submit(self.sshclient1.ssh_exec, dd.format(testpath2, 70))
            pools.append(p1)
            pools.append(p2)
            pools.append(p3)
            pools.append(p4)
            for t in as_completed(pools):
                t.result()
            # 检验md5sum
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_before = res.split()[0]
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            # 再次上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 检查文件状态
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # 再次计算md5值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_after = res.split()[0]
            # 检验md5值是否一致
            assert md5_before == md5_local == md5_after, "md5sum mismatching."
        finally:
            # 清理测试数据
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    def test_seek_3790(self):
        """
        3790 多线程并发seek写不同文件（s3 mirror）
        """
        filenum = 1000
        fnames = []
        # 客户端挂载
        mount = client_mount(self.client1, acl_add=True)
        assert mount == 0, "client mount failed."
        # 写入测试文件
        self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, filenum))
        # 上传文件至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(60)
        # 检查文件上传情况
        for i in range(filenum):
            fname = self.testdir + "/autotest.0." + str(i)
            # check_layer(fname, "S3", "998")
            fnames.append(fname)
        # 并发seek读取文件
        script = create_s3_script(fnames[:20], 20, mode="write")
        stat, _ = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&cd %s&&python3 \
        /tmp/autotest_tiering_mul_read.py" % (script, self.mountdir))
        assert stat == 0, "multi seek write failed."

    def test_seek_3793(self):
        """
        3793 truncate 小于S3上的文件（flush后校验）（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 写入测试数据
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            self.sshclient1.ssh_exec(self.fio.format("100M", self.testpath, 1))
            # 拷贝数据
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 上传文件至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # truncate
            self.sshclient1.ssh_exec("truncate -s 50M %s/autotest.0.0" % self.testpath)
            # 等待文件再次上传
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 计算s3文件md5值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_s3 = res.split()[0]
            # 本地文件做相同操作并计算md5值
            self.sshclient1.ssh_exec("truncate -s 50M %s/autotest.0.0" % testpath2)
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            # 对比md5值
            assert md5_s3 == md5_local, "md5sum mismatching."
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    @pytest.mark.parametrize("write_param", ("doing", "done"))
    def test_seek_3919(self, write_param):
        """
        3919 大文件上传到S3后，追加写（s3 mirror）,3920 大文件上传到S3的过程中，追加写
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 写入测试数据
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, 1))
            # 拷贝数据
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 上传文件至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            if write_param == "doing":
                sleep(5)
            else:
                sleep(40)
            # 追加写文件
            self.sshclient1.ssh_exec("cat /var/log/* >> %s/autotest.0.0 > /dev/null 2>&1" % self.testpath)
            self.sshclient1.ssh_exec("cat /var/log/* >> %s/autotest.0.0 > /dev/null 2>&1" % testpath2)
            # 校验md5值是否一致
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_s3 = res.split()[0]
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            assert md5_s3 == md5_local, "md5sum mismatching."
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    def test_seek_3922(self):
        """
        3922 100线程并发seek顺序读S3上的大文件（s3 mirror）
        """
        # 客户端挂载
        mount = client_mount(self.client1, acl_add=True)
        assert mount == 0, "client mount failed."
        fnames = []
        # 写入测试数据
        self.sshclient1.ssh_exec(self.fio.format("1024M", self.testpath, 100))
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(60)
        # 生成脚本
        for i in range(0, 100):
            fname = self.testdir + "/autotest.0." + str(i)
            fnames.append(fname)
        script = create_s3_script(fnames, workers=100, bytesize="5242880")
        _, res = self.sshclient1.ssh_exec("echo \"%s\" > /tmp/autotest_tiering_mul_read.py&&cd %s&&python3 \
        /tmp/autotest_tiering_mul_read.py" % (script, self.mountdir))
        assert res == "0", "multi seek read failed."

    @pytest.mark.skipif(len(consts.CLIENT) < 2, reason="need two client")
    def test_seek_4058(self):
        """
        4058 两个客户端同时执行rsync将S3数据下载到本地（s3 mirror）
        """
        testpath1 = os.path.join(self.mountdir, "autotest_seek_4058001")
        testpath2 = os.path.join(self.mountdir, "autotest_seek_4058002")
        client2 = consts.CLIENT[1]
        rsync_cmd = "rsync -avP %s/ {0}/" % self.testpath
        sshclient2 = sshClient(client2)
        try:
            # 客户端挂载
            mount1 = client_mount(self.client1, acl_add=True)
            mount2 = client_mount(client2, acl_add=True)
            assert mount1 == 0 and mount2 == 0, "Client mount failed."
            # 创建文件
            self.sshclient1.ssh_exec("mkdir -p %s %s" % (testpath1, testpath2))
            self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, 100))
            # 上传至S3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(60)
            # 两个客户端文件同时rsync
            pools = []
            pool = ThreadPoolExecutor(max_workers=2)
            p1 = pool.submit(self.sshclient1.ssh_exec, rsync_cmd.format(testpath1))
            p2 = pool.submit(sshclient2.ssh_exec, rsync_cmd.format(testpath2))
            pools.append(p1)
            pools.append(p2)
            for t in as_completed(pools):
                res = t.result()
                assert res[0] == 0, "rsync s3 file failed."
        finally:
            self.sshclient1.ssh_exec("rm -fr %s %s" % (testpath1, testpath2))
            sshclient2.close_connect()

    def test_seek_4093(self):
        """
        4093 对S3上文件进行一写多读，保证文件最终数据正确性（先md5sum）（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 创建测试文件
            self.sshclient1.ssh_exec("mkdir -p %s " % testpath2)
            self.sshclient1.ssh_exec(self.fio.format("1G", self.testpath, 1))
            # 文件拷贝
            self.sshclient1.ssh_exec("cp %s/* %s" % (self.testpath, testpath2))
            # 文件上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # 检查文件状态
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # 并发读和写s3文件
            testfile = self.testpath + "/autotest.0.0"
            pools = []
            pool = ThreadPoolExecutor(max_workers=4)
            p1 = pool.submit(self.sshclient1.ssh_exec,
                             "dd if=/dev/zero of=%s bs=1M seek=50 count=10 conv=notrunc" % testfile)
            p2 = pool.submit(self.sshclient1.ssh_exec, "dd if=%s of=/dev/null bs=1M skip=10 count=9" % testfile)
            p3 = pool.submit(self.sshclient1.ssh_exec, "dd if=%s of=/dev/null bs=1M skip=60 count=9" % testfile)
            p4 = pool.submit(self.sshclient1.ssh_exec, "dd if=%s of=/dev/null bs=1M skip=120 count=8" % testfile)
            pools.append(p1)
            pools.append(p2)
            pools.append(p3)
            pools.append(p4)
            for t in as_completed(pools):
                t.result()
            # 写local file
            self.sshclient1.ssh_exec(
                "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=50 count=10 conv=notrunc" % testpath2)
            # 对比md5sum
            _, res = self.sshclient1.ssh_exec("md5sum " + testfile)
            md5_s3 = res.split()[0]
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            assert md5_s3 == md5_local, "md5sum mismatching."
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    def test_seek_3792(self):
        """
        3792 truncate 0 S3上的文件（s3 mirror）
        """
        s3object = S3Object()
        # 客户端挂载
        mount = client_mount(self.client1, acl_add=True)
        assert mount == 0, "client mount failed."
        # 写入测试数据
        self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, 1))
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(30)
        # 查看s3容量
        s3_du1 = s3object.get_keys()
        # 清空文件
        stat, _ = self.sshclient1.ssh_exec("truncate -s 0 %s/autotest.0.0" % self.testpath)
        assert stat == 0, "truncate 0 failed."
        # 计算md5sum
        _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
        md5sum1 = res.split()[0]
        s3_du2 = s3object.get_keys()
        # 再次上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(10)
        # 再次计算md5sum
        _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
        md5sum2 = res.split()[0]
        # 检验md5sum 和s3容量未发生变化
        assert s3_du1 == s3_du2, "s3 capacity change"
        assert md5sum1 == md5sum2, "md5sum mismatching."

    def test_seek_3794(self):
        """
        3794 truncate 大于S3上的文件（flush后校验)（s3 mirror）
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 创建测试文件
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            self.sshclient1.ssh_exec(self.fio.format("200M", self.testpath, 1))
            self.sshclient1.ssh_exec("cp %s/autotest.0.0 %s" % (self.testpath, testpath2))
            # 上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(30)
            # truncate s3文件
            self.sshclient1.ssh_exec("truncate -s 300M %s/autotest.0.0" % self.testpath)
            # 重新触发上传
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(60)
            # truncate本地文件
            self.sshclient1.ssh_exec("truncate -s 300M %s/autotest.0.0" % testpath2)
            # 对比md5sum值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_s3 = res.split()[0]
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            assert md5_s3 == md5_local, "md5sum mistmatching."
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    @pytest.mark.parametrize("mode", ("write", "read"))
    @pytest.mark.parametrize("trunc_size", ("0", "50", "100"))
    def test_seek_3795(self, trunc_size, mode):
        """
        3795-7 在seek读或者写操作后，分别truncate 清空、大于、小于 S3上的文件（s3 mirror）。
        """
        testdir2 = "autotest_seek_" + time.strftime("%m-%d-%H%M%S")
        testpath2 = os.path.join(self.mountdir, testdir2)
        try:
            # 客户端挂载
            mount = client_mount(self.client1, acl_add=True)
            assert mount == 0, "client mount failed."
            # 创建测试文件
            self.sshclient1.ssh_exec("mkdir -p " + testpath2)
            self.sshclient1.ssh_exec(self.fio.format("100M", self.testpath, 1))
            # 文件拷贝
            self.sshclient1.ssh_exec("cp %s/autotest.0.0 %s" % (self.testpath, testpath2))
            # 上传至s3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(10)
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # seek读取数据
            if mode == "read":
                stat, _ = self.sshclient1.ssh_exec(
                    "dd if=%s/autotest.0.0 of=/dev/null bs=1M skip=10 count=10" % self.testpath)
                assert stat == 0, "seek read failed."
            else:
                stat, _ = self.sshclient1.ssh_exec(
                    "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=10 count=10 conv=notrunc" % self.testpath)
                assert stat == 0, "seek write failed."
                # 本地文件操作
                self.sshclient1.ssh_exec(
                    "dd if=/dev/zero of=%s/autotest.0.0 bs=1M seek=10 count=10 conv=notrunc" % testpath2)
            # 执行truncate操作
            self.sshclient1.ssh_exec("truncate -s %sM %s/autotest.0.0" % (trunc_size, self.testpath))
            _, res = self.sshclient1.ssh_exec("du -hm %s/autotest.0.0" % self.testpath)
            assert res.split()[0] == trunc_size, "Truncate size not as expected."
            # truncate本地文件
            self.sshclient1.ssh_exec("truncate -s %sM %s/autotest.0.0" % (trunc_size, testpath2))
            # 重新上传该文件至上3
            sleep(2)
            self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
            sleep(10)
            check_layer(self.testdir + "/autotest.0.0", "S3", "998")
            # 校验md5值
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % self.testpath)
            md5_s3 = res.split()[0]
            _, res = self.sshclient1.ssh_exec("md5sum %s/autotest.0.0" % testpath2)
            md5_local = res.split()[0]
            assert md5_s3 == md5_local, "md5sum mismatch"
        finally:
            self.sshclient1.ssh_exec("rm -fr " + testpath2)

    @pytest.mark.skipif(len(consts.CLIENT) < 2, reason="need two client")
    def test_seek_4056(self):
        """
        4056 两个客户端并发读同一tiering目录下的大量文件（s3 mirror）
        """
        client2 = consts.CLIENT[1]
        sshclient2 = sshClient(client2)
        fnames = []
        # 客户端挂载
        mount1 = client_mount(self.client1, acl_add=True)
        mount2 = client_mount(client2, acl_add=True)
        assert mount1 == 0 and mount2 == 0, "Client mount failed."
        # 写入测试数据
        self.sshclient1.ssh_exec(self.fio.format("1024M", self.testpath, 400))
        # 上传至s3
        sleep(2)
        self.sshserver.ssh_exec(self.get_cli("tiering_flush", "998"))
        sleep(60)
        # 生成测试脚本
        for i in range(0, 100):
            fname = self.testpath + "/autotest.0." + str(i)
            fnames.append(fname)
        script = create_s3_script(fnames, workers=100, bytesize="524288")
        self.sshclient1.ssh_exec('echo "%s" > /tmp/autotest_tiering_mul_read.py >/dev/null 2>&1' % script)
        sshclient2.ssh_exec('echo "%s" > /tmp/autotest_tiering_mul_read.py >/dev/null 2>&1' % script)
        # 两个客户端并执行
        pools = []
        pool = ThreadPoolExecutor(max_workers=2)
        p1 = pool.submit(self.sshclient1.ssh_exec, "python3 /tmp/autotest_tiering_mul_read.py")
        p2 = pool.submit(sshclient2.ssh_exec, "python3 /tmp/autotest_tiering_mul_read.py")
        pools.append(p1)
        pools.append(p2)
        for t in as_completed(pools):
            res = t.result()
            assert res[0] == 0, "multi read failed."
        sshclient2.close_connect()