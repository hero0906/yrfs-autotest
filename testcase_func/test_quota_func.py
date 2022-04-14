# coding=utf-8

"""
@Description : quota dir function case
@Time : 2020/12/15 18:58
@Author : cays
"""

import os
import pytest
from time import sleep
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec, sshClient, read_config
from depend.skip_mark import verify_mount_point

server = consts.META1
conf = read_config('test_quota_func')


@pytest.fixture(scope="class", params=conf)
def data_init(request):
    param = request.param
    yield param


@pytest.mark.funcTest
class TestfuncMove(YrfsCli):

    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)

        self.test_dir = "autotest_quota"
        self.test_path = os.path.join(consts.MOUNT_DIR, self.test_dir)

        self.test_dira = self.test_dir + "/a"
        self.test_patha = self.test_path + "/a"

        self.test_dirb = self.test_dir + "/a/b"
        self.test_pathb = self.test_path + "/a/b"

        self.test_dirc = self.test_dir + "/a/b/c"
        self.test_pathc = self.test_path + '/a/b/c'

        self.test_dird = self.test_dir + "/a/b/d"
        self.test_pathd = self.test_path + '/a/b/d'

        self.test_dirf = self.test_dir + "/a/b/f"
        self.test_pathf = self.test_path + '/a/b/f'

        self.test_dirq = self.test_dir + "/a/b/c/q"
        self.test_pathq = self.test_path + '/a/b/c/q'

        self.test_diri = self.test_dir + "/a/b/f/i"
        self.test_pathi = self.test_path + '/a/b/f/i'

        self.test_dirh = self.test_dir + "/a/b/e/h"
        self.test_pathh = self.test_path + '/a/b/e/h'

        self.quota_del = "yrcli --projectquota --op=delete --path={0} -u"

    def setup(self):
        # 创建初始化测试目录
        ssh2 = sshClient(server)
        ssh2.ssh_exec('rm -fr ' + self.test_path)
        # 创建quota目录结构
        # 创建一级目录设置quota
        ssh2.ssh_exec('mkdir -p ' + self.test_patha)
        cmd_set1 = self.get_cli('quota_set', self.test_dira, '200M', '100')
        ssh2.ssh_exec(cmd_set1)
        # 创建二级目录设置quota
        ssh2.ssh_exec('mkdir ' + self.test_pathb)
        cmd_set2 = self.get_cli('quota_set', self.test_dirb, '200M', '100')
        ssh2.ssh_exec(cmd_set2)
        # 创建三级目录并设置quota
        ssh2.ssh_exec('mkdir ' + self.test_pathc)
        cmd_set3 = self.get_cli('quota_set', self.test_dirc, '200M', '100')
        ssh2.ssh_exec(cmd_set3)

        ssh2.ssh_exec('mkdir ' + self.test_pathd)
        cmd_set4 = self.get_cli('quota_set', self.test_dird, '200M', '100')
        ssh2.ssh_exec(cmd_set4)
        # 创建四级目录并设置quota
        ssh2.ssh_exec('mkdir ' + self.test_pathq)
        cmd_set5 = self.get_cli('quota_set', self.test_dirq, '200M', '100')
        ssh2.ssh_exec(cmd_set5)

        ssh2.ssh_exec('mkdir -p ' + self.test_pathi)
        cmd_set6 = self.get_cli('quota_set', self.test_diri, '200M', '100')
        ssh2.ssh_exec(cmd_set6)

        ssh2.ssh_exec('mkdir -p ' + self.test_pathh)
        ssh2.close_connect()
        sleep(10)

    def teardown(self):
        # 清除测试目录
        sleep(10)
        ssh2 = sshClient(server)
        ssh2.ssh_exec(self.quota_del.format(self.test_dira))
        ssh2.ssh_exec(self.quota_del.format(self.test_dirb))
        ssh2.ssh_exec(self.quota_del.format(self.test_dirc))
        ssh2.ssh_exec(self.quota_del.format(self.test_dird))
        ssh2.ssh_exec(self.quota_del.format(self.test_dirq))
        ssh2.ssh_exec(self.quota_del.format(self.test_diri))
        ssh2.ssh_exec('rm -fr ' + self.test_path)
        ssh2.close_connect()
        # pass

    # @pytest.mark.skip()
    def test_fourdir_move_onequotadir(self, data_init):
        """
        caseID:3017 四级非quota目录移动到一级quota目录下
        """
        sleep(10)
        ssh2 = sshClient(server)
        _, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathh, self.test_patha))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"

    # @pytest.mark.skip()
    def test_fourquotadir_move_onequotadir(self, data_init):
        """
        caseID:3013 四级quota目录移动到一级quota目录下，失败
        """
        sleep(10)
        ssh2 = sshClient(server)
        _, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathq, self.test_patha))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"

    # @pytest.mark.skip()
    def test_fourdir_move_twoquotadir(self, data_init):
        """
        caseID:3016 四级非quota目录移动二级quota目录下,成功
        """
        sleep(10)
        ssh2 = sshClient(server)
        stat, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathh, self.test_pathb))
        ssh2.close_connect()
        assert stat == 0, "mv success"

    # @pytest.mark.skip()
    def test_fourquotadir_move_twoquotadir(self, data_init):
        """
        caseID:3012 四级quota目录移动到二级quota目录下，失败
        """
        sleep(10)
        ssh2 = sshClient(server)
        _, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathq, self.test_pathb))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"

    # @pytest.mark.skip()
    def test_fourdir_move_threequotadir(self, data_init):
        """
        caseID: 3015 四级非quota目录移动到三级quota目录下，失败
        """
        sleep(10)
        ssh2 = sshClient(server)
        _, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathh, self.test_pathd))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"

    # @pytest.mark.skip()
    def test_fourdir_move_threedir(self):
        """
        caseID: 3014 四级非quota目录移动到三级非quota目录下，成功
        """
        sleep(10)
        ssh2 = sshClient(server)
        stat, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathh, self.test_pathf))
        ssh2.close_connect()
        assert stat == 0, "mv success"

    # @pytest.mark.skip()
    def test_fourquotadir_move_threedir(self, data_init):
        """
        caseID: 3011 四级quota目录移动三级非quota目录下
        """
        sleep(10)
        ssh2 = sshClient(server)
        stat, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathq, self.test_patha))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"

    # @pytest.mark.skip()
    def test_fourquotadir_move_threequotadir(self, data_init):
        """
        caseID: 3010 四级quota目录移动到三级quota目录下
        """
        sleep(10)
        ssh2 = sshClient(server)
        _, res = ssh2.ssh_exec('mv %s %s' % (self.test_pathq, self.test_pathd))
        ssh2.close_connect()
        assert data_init['notpermit'] in res, "mv failed"


@pytest.mark.funcTest
class TestnoMirror(YrfsCli):

    def setup_class(self):

        self.space = "2048M"
        self.inode = 10
        self.testdir = "autotest_quota"
        self.path = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.quota_del = "yrcli --projectquota --op=delete --path={0} -u"

    def test_quota_nomirror(self, data_init):
        """
        caseID:3009 单副本目录quota上限测试
        """
        # 创建单副本目录
        sleep(10)
        ssh2 = sshClient(server)
        try:
            make_dir = self.get_cli('mkdir', self.testdir, 'nomirror')
            ssh2.ssh_exec(make_dir)
            set_quota = self.get_cli('quota_set', self.testdir, self.space, self.inode)
            _, res3 = ssh2.ssh_exec(set_quota)

            count = int(self.space[:-1])
            sleep(10)
            dd = "dd if=/dev/zero of=%s/autotest_file1 bs=1M count=%s" % (self.path, count)
            _, res1 = ssh2.ssh_exec(dd)

            sleep(10)
            dd = "dd if=/dev/zero of=%s/autotest_file2 bs=1M count=%s" % (self.path, count)
            _, res2 = ssh2.ssh_exec(dd)

            assert "copied" in res1
            assert data_init['limiterror'] in res2
            assert data_init['success'] in res3

        finally:
            ssh2.ssh_exec(self.quota_del.format(self.testdir))
            ssh2.ssh_exec("rm -fr %s" % self.path)
            ssh2.close_connect()


@pytest.mark.funcTest
class TestquotaFunc(YrfsCli):
    """
    单节点quota功能测试
    """

    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)
        self.space = "2048M"
        self.inode = 10
        self.testdir = "autotest_quota"
        self.path = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.quota_del = "yrcli --projectquota --op=delete --path={0} -u"

    def setup(self):
        ssh2 = sshClient(server)
        sleep(10)
        ssh2.ssh_exec(self.quota_del.format(self.testdir))
        ssh2.ssh_exec("mkdir -p %s" % self.path)
        ssh2.ssh_exec(self.get_cli('quota_set', self.testdir, self.space, self.inode))
        ssh2.close_connect()
        sleep(10)

    def teardown(self):
        sleep(10)
        ssh_exec(server, self.quota_del.format(self.testdir))
        ssh_exec(server, "rm -fr %s*" % self.path)

    def test_move_file(self, data_init):
        """
        caseID: 3008 quota目录下的文件移动
        """
        # 设置目录quota配置
        # sleep(10)
        ssh2 = ""
        try:
            ssh2 = sshClient(server)

            testpath2 = self.path + "02"
            # ssh_exec(server, "mkdir -p %s" % self.path)
            ssh2.ssh_exec("mkdir -p %s" % testpath2)
            sleep(10)
            _, res1 = ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file1 bs=1M count=1" % self.path)
            stat2, res2 = ssh2.ssh_exec("mv %s/autotest_file1 %s" % (self.path, testpath2))
            # 删除测试目录
            sleep(10)
        finally:
            # ssh.ssh_exec("rm -fr %s" % (self.path))
            # ssh.ssh_exec("rm -fr %s" % (testpath2))
            ssh2.close_connect()
        # 验证结果正确性

        assert "copied" in res1
        assert stat2 != 0

    def test_quota_subdir_mv(self):
        """
        bugID: 4160 quota目录下深层次无法移动文件,预期需要可移动。
        """
        ssh2 = sshClient(server)
        try:
            testdir1 = self.path + "/dir1/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11" \
                                   "/dir12/dir13/dir14/dir15/dir16/dir17/dir18/"
            testdir2 = self.path + "/dir1/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11" \
                                   "/dir12/dir13/dir14/dir15/dir16"
            # 深目录创建
            mk_stat, _ = ssh2.ssh_exec("mkdir -p " + testdir1)
            # 目录移动
            mv_stat, _ = ssh2.ssh_exec("mv %s %s" % (testdir1, testdir2))
        finally:
            ssh2.close_connect()
        # 验证mv是否正确
        assert mk_stat == 0, "mkdir %s failed."
        assert mv_stat == 0, "mv failed."

    def test_limitup_shrink(self, data_init):
        """
        caseID: 3006 quota limit达到上限后，缩小limit设置失败
        """
        ssh2 = sshClient(server)
        try:
            count = int(self.space[:-1])
            # quota目录写满数据
            _, res1 = ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file1 bs=1M count=%s" % (self.path, count))
            sleep(10)
            # 缩小quota目录配置
            _, res2 = ssh2.ssh_exec(
                self.get_cli('quota_set', self.testdir, str(int(int(count) / 2)) + "M", int(self.inode / 2)))
            # 删除测试目录
        # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()
        assert "copied" in res1
        assert data_init['failed'] in res2

    def test_limitup_expand(self):
        """
        caseID: 3005 quota limit达到上限后，扩大limit设置数据写入测试
        """
        ssh2 = sshClient(server)
        try:
            count = self.space[:-1]
            # 写满quota数据
            _, res1 = ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file1 bs=1M count=%s" % (self.path, count))
            # 增大quota配置继续写入数据
            ssh2.ssh_exec(self.get_cli('quota_update', self.testdir, str(int(count) * 2) + "M", self.inode))
            sleep(10)
            _, res2 = ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file2 bs=1M count=%s" % (self.path, count))
        # 删除测试目录
        # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()

        assert "copied" in res1
        assert "copied" in res2

    # @pytest.mark.skip()
    def test_multidir_limitup(self, data_init):
        """
        caseID: 3004 两级quota目录多子目录 limit上限测试
        """
        ssh2 = sshClient(server)
        try:
            # 设置子目录quota
            ssh2.ssh_exec("mkdir -p %s/dir{1..4}" % self.path)
            _, res4 = ssh2.ssh_exec(self.get_cli('quota_set', self.testdir + "/dir1", self.space, self.inode))
            assert "Success" in res4
            _, res5 = ssh2.ssh_exec(self.get_cli('quota_set', self.testdir + "/dir2", self.space, self.inode))
            assert "Success" in res5
            _, res6 = ssh2.ssh_exec(self.get_cli('quota_set', self.testdir + "/dir3", self.space, self.inode))
            assert "Success" in res6
            _, res7 = ssh2.ssh_exec(self.get_cli('quota_set', self.testdir + "/dir4", self.space, self.inode))
            assert "Success" in res7
            count = self.space[:-1]
            # 写入部分目录使之达到上限
            ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file bs=1M count=%s" % (self.path + "/dir1", int(count)))
            ssh2.ssh_exec("touch %s/testfile{1..%s}" % (self.path + "/dir3", self.inode))
            # 达到上限后再次写入测试
            sleep(10)
            _, res1 = ssh2.ssh_exec(
                "dd if=/dev/zero of=%s/autotest_file1 bs=1M count=%s" % (self.path + "/dir2", int(count)))
            _, res2 = ssh2.ssh_exec("touch %s/testfile9999" % (self.path + "/dir4"))
            # 删除测试目录
        # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()

        assert data_init['limiterror'] in res1
        assert data_init['limiterror'] in res2

    def test_rename_quotadir(self):
        """
        caseID: 2999 设置quota后重命名该目录quota依然生效
        """
        ssh2 = sshClient(server)
        testdir2 = self.testdir + "02"
        testpath2 = self.path + "02"
        try:
            # 重命名目录
            ssh2.ssh_exec("mv %s %s" % (self.path, testpath2))
            stat, res = ssh2.ssh_exec(self.get_cli('quota_single_list', testdir2))
            # 删除测试目录
            # sleep(10)
            # ssh.ssh_exec("rm -fr %s" % (testpath2))
        finally:
            sleep(5)
            ssh2.ssh_exec(self.quota_del.format(testdir2))
            ssh2.close_connect()
        # 验证结果的正确性
        assert stat == 0

    def test_samename_recreate(self):
        """
        caseID: 2998 quota同名目录删除重建
        """
        # 删除目录
        ssh2 = sshClient(server)
        try:
            ssh2.ssh_exec("rm -fr %s" % self.path)
            sleep(10)
            # 重新创建同名目录
            ssh2.ssh_exec("mkdir -p %s" % self.path)
            status, _ = ssh2.ssh_exec(self.get_cli('quota_single_list', self.testdir))
            # 删除测试目录
            # sleep(10)
            # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()
        assert status != 0
        # 验证结果的正确性

    def test_setsubdir_uplimit_parentdir(self, data_init):
        """
        caseID: 2997 验证设置子目录quota超过父目录设置不成功
        """
        ssh2 = sshClient(server)
        try:
            count = int(self.space[:-1])
            test_subdir = self.path + "/dir1"
            # sleep(10)
            # 创建父目录并设置quota
            # ssh_exec(server, "mkdir -p %s" % self.path)
            # res1 = ssh_exec(server, self.get_cli('quota_set', self.testdir, self.space, self.inode))
            # leep(10)
            # 创建子目录并设置quota
            ssh2.ssh_exec("mkdir -p %s" % test_subdir)
            stat, res = ssh2.ssh_exec(
                self.get_cli('quota_set', self.testdir + "/dir1", str(count * 2) + "M", self.inode * 2))
        # 清除测试目录
        # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()
        # assert "Success" in res1
        assert stat != 0, "quota set success."

    def test_sixteen_subdir(self, data_init):
        """
        caseID: 2996 验证最大目录深度quota limit设置
        """
        ssh2 = sshClient(server)
        try:
            test_subdir1 = self.testdir + "/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14" \
                                          "/dir15/dir16 "
            test_subpath1 = self.path + "/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14/dir15" \
                                        "/dir16 "
            test_subdir2 = self.testdir + "/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14" \
                                          "/dir15/dir16/dir17 "
            test_subpath2 = self.path + "/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14/dir15" \
                                        "/dir16/dir17 "

            ssh2.ssh_exec("mkdir -p " + test_subpath1)
            _, res1 = ssh2.ssh_exec(self.get_cli('quota_set', test_subdir1, self.space, self.inode))
            ssh2.ssh_exec("mkdir -p " + test_subpath2)
            _, res2 = ssh2.ssh_exec(self.get_cli('quota_set', test_subdir2, self.space, self.inode))
            sleep(10)
            # 清除测试目录
            # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()

        assert data_init['success'] in res1
        assert data_init['sixteendepths'] in res2

    def test_parentdir_recycle(self, data_init):
        """
        caseID: 2994 两级quota目录子目录删除，父目录配额正确回收
        """
        ssh2 = sshClient(server)
        try:
            count = int(self.space[:-1])
            subdir = self.testdir + "/dir1"
            subpath = self.path + "/dir1"
            # 配置子目录quota
            ssh2.ssh_exec("mkdir -p " + subpath)
            _, res1 = ssh2.ssh_exec(self.get_cli('quota_set', subdir, self.space, self.inode))
            _, res2 = ssh2.ssh_exec("dd if=/dev/zero of=%s/autotest_file bs=1M count=%s" % (subpath, int(count / 20)))
            sleep(10)
            ssh2.ssh_exec(self.quota_del.format(subdir))
            ssh2.ssh_exec("rm -fr " + subpath)
            sleep(10)
            _, res3 = ssh2.ssh_exec(self.get_cli('quota_single_list', self.testdir) + "|tail -n 1")
            # 清除测试目录
            # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh2.close_connect()

        assert data_init['success'] in res1
        assert "copied" in res2
        assert res3.split()[2] == "0.0B"

    def test_update_parentdir_less_subdir(self, data_init):
        """
        caseID: 2993 验证两级目录修改父目录quota小于子目录时不成功
        """
        ssh2 = sshClient(server)
        subdir = self.testdir + "/dir1"
        subpath = self.path + "/dir1"
        try:
            ssh2.ssh_exec('mkdir ' + subpath)
            ssh2.ssh_exec(self.get_cli('quota_set', subdir, self.space, self.inode))
            sleep(10)
            # 修改父目录quota值小于子目录值数值
            count = int(self.space[:-1])
            stat, res = ssh2.ssh_exec(
                self.get_cli('quota_update', self.testdir, str(int(count / 2)) + "M", int(self.inode / 2)))
            #ssh2.ssh_exec("rm -fr %s" % self.path)
            sleep(10)
        finally:
            ssh2.ssh_exec(self.quota_del.format(subdir))
            ssh2.ssh_exec(self.quota_del.format(self.testdir))
            ssh2.close_connect()
        assert stat != 0
        # assert data_init['setfail'] in res

    def test_expand_parentdir(self):
        """
        caseID: 2992 验证两级目录增大父目录quota对子目录无影响
        """
        ssh2 = sshClient(server)
        try:
            # 创建子目录quota
            subdir = self.testdir + "/dir1"
            subpath = self.path + "/dir1"
            ssh2.ssh_exec('mkdir ' + subpath)
            ssh2.ssh_exec(self.get_cli('quota_set', subdir, self.space, self.inode))
            sleep(10)
            # 更新父目录quota信息
            space = str(int(self.space[:-1]) * 2) + "M"
            inode = self.inode * 2
            ssh2.ssh_exec(self.get_cli('quota_update', self.testdir, space, inode))
            # 查询更新后的子目录quota信息
            _, res1 = ssh2.ssh_exec(self.get_cli('quota_single_list', subdir) + "|tail -n 1")
            # 查询父目录修改的值是否正确
            _, res2 = ssh2.ssh_exec(self.get_cli('quota_single_list', self.testdir) + "|tail -n 1")
            # 清除quota测试目录
            # ssh.ssh_exec("rm -fr %s" % (self.path))
            # 关闭ssh连接
        finally:
            ssh2.close_connect()
        # 验证子目录quota信息
        assert res1.split()[3] == '2.0GiB'
        assert int(res1.split()[5]) == self.inode
        # 验证父目录quota信息
        assert res2.split()[3] == '4.0GiB'
        assert int(res2.split()[5]) == inode

    def test_quota_info_check(self):
        """
        caseID: 2990 验证数据写入统计信息正确
        """
        ssh = sshClient(server)
        try:
            count = int(self.space[:-1])
            # 写入大文件和空文件
            ssh.ssh_exec("dd if=/dev/zero of=%s/testfile bs=1M count=%s" % (self.path, count))
            ssh.ssh_exec("touch %s/testfile{1..%s}" % (self.path, self.inode - 1))
            sleep(10)
            # 查询并验证实际使用quota与统计quota信息是否匹配
            _, res = ssh.ssh_exec(self.get_cli('quota_single_list', self.testdir) + "|tail -n 1")
            # ssh.ssh_exec("rm -fr %s" % (self.path))
        finally:
            ssh.close_connect()
        assert res.split()[2] == '2.0GiB'
        # 统计数据加入了自身的inode所以需要+1
        assert int(res.split()[4]) == self.inode + 1
