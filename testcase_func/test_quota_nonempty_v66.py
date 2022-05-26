# coding=utf-8
"""
@Desciption : quota nonempty dir test
@Time : 2020/5/27 18:47
@Author : caoyi
"""
import pytest
import logging
from time import sleep
import random
import time
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from depend.client import client_mount
from common.cluster import get_entry_info

yrfs_version = int(consts.YRFS_VERSION[:2])

logger = logging.getLogger(__name__)

#@pytest.mark.skip(msg="skip")
class TestquotanonEmpty(YrfsCli):
    '''
    非空目录quota用例集
    '''
    def setup_class(self):
        #这些用例只在6.6版本以上可以执行
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.quota_error_info = "Disk quota exceeded"

        if yrfs_version < 66:
            logger.error("yrfs version lower than 660 cannt't run.")
            pytest.skip(msg="only 66* verison need run, skip", allow_module_level=True)
        #quota 命令参数获取
        self.add_quota = self.get_cli(self, "nquota_add")
        self.quota_verbose = self.get_cli(self, "quota_list_verbose")
        self.update_quota = self.get_cli(self, "quota_update")
        self.delete_quota = self.get_cli(self, "quota_remove")
        self.add_ignore_quota = self.get_cli(self, "noquota_add_ignore")
        #mdtest测试参数
        self.mdtest = "mdtest -C -d {0} -i 1 -w 1 -I 50000 -z 0 -b 0 -L -F"

    def setup(self):
        self.testdir = "autotest_non_quota_" + time.strftime("%m-%d-%H%M%S")
        self.testpath = consts.MOUNT_DIR + "/" + self.testdir
        self.sshserver = sshClient(self.serverip)
        self.sshclient = sshClient(self.clientip)
        #创建测试目录
        self.sshserver.ssh_exec("rm -fr {0}&&mkdir {0}".format(self.testpath))
        sleep(5)

    def teardown(self):
        sleep(5)
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    @pytest.mark.parametrize("layer", ("one", "two", "three"))
    def test_quota_7976(self, layer):
        """
        7976 校验不同层级目录均设quota，删除父目录quota，查看子目录得quota id未更改
        """
        subpath = self.testpath + "/A/B/C"
        dir1 = self.testdir + "/A"
        dir2 = self.testdir + "/A/B"
        dir3 = self.testdir + "/A/B/C"
        self.sshserver.ssh_exec("mkdir -p " + subpath)
        #设置quota,分别判断不同层级目录的删除情况是否正常
        self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "200M", "150"))
        check_dir = dir1
        if layer == "two" or layer == "three":
            self.sshserver.ssh_exec(self.add_ignore_quota.format(dir1, "200M", "150"))
            check_dir = dir2
        if layer == "three":
            self.sshserver.ssh_exec(self.add_ignore_quota.format(dir2, "200M", "150"))
            check_dir = dir3
        #获取子目录prjid
        entry_info = get_entry_info(check_dir)
        prjid_old = entry_info["ProjectID"]
        #父目录的projectquota删除
        sleep(5)
        self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
        check_dir = dir1
        if layer == "two" or layer == "three":
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            check_dir = dir2
        if layer == "three":
            self.sshserver.ssh_exec(self.delete_quota.format(dir1))
            check_dir = dir3
        #再次查看子目录的prjid
        entry_info = get_entry_info(check_dir)
        prjid_new = entry_info["ProjectID"]
        #比对两次的pjdid一样
        assert prjid_old == prjid_new, "prjid was changed"

    def test_add_little_file(self):
        '''
        caseID: 3660 （非空目录quota）目录中200个文件设置quota成功
        '''
        # caseID: 3679 （非空目录quota）更新quota目录设置
        # caseID: 3674 （非空目录quota）非空目录设置删除后再次设置
        # caseID: 3680 （非空目录quota）目录rename后正常显示
        # caseID: 3662 （非空目录quota）文件数量未超过quota数值目录设置后可以继续写入
        try:
            #客户端挂载目录
            inode = "100"
            self.sshserver.ssh_exec(self.get_cli("acl_ip_add", self.testdir, "*", "rw"))
            mount_stat = client_mount(self.clientip, subdir=self.testdir)
            if mount_stat != 0:
                pytest.skip(msg="client mount failed, test skip.")
            #1.非空目录设置测试
            #填充文件
            logger.info("set non empty dir quota.")
            self.sshclient.ssh_exec("mkdir -p %s/dir{1..97}" % self.testpath)
            self.sshclient.ssh_exec("dd if=/dev/zero of=%s/file1 bs=1M count=%s oflag=direct" % (self.testpath, inode))
            sleep(5)
            #add quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "200M", "150"))
            sleep(5)
            #查看quota used信息是否正确
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            dirused = list_res[9]
            fileused = list_res[10]

            assert add_stat == 0, "add quota failed."
            assert list_stat == 0, 'list quota verbose failed.'
            assert spaceused == "100MiB"
            assert inodeused == "100"
            assert dirused == "99"
            assert fileused == "1"
            #2.写入上限验证测试
            logger.info("quota limit test.")
            _, dd_res = self.sshclient.ssh_exec("dd if=/dev/zero of=%s/file2 bs=1M count=100 oflag=direct" % self.testpath)
            touch_stat, _ = self.sshclient.ssh_exec("touch %s/touch{1..50}" % self.testpath)
            #检验文件可以正常写入
            assert "copied" in dd_res, "dd file failed."
            assert touch_stat == 0, "file touch failed."
            sleep(5)
            #3.验证达到limit上限后无法继续写入
            _, dd_res = self.sshclient.ssh_exec("dd if=/dev/zero of=%s/file3 bs=1M count=100 oflag=direct" % self.testpath)
            touch_stat, _ = self.sshclient.ssh_exec("touch %s/touch_exceed1" % self.testpath)
            assert self.quota_error_info in dd_res, "dd file success."
            assert touch_stat != 0, "touch file success."
            #4.更新目录quota设置
            logger.info("update quota test.")
            update_stat, _ = self.sshserver.ssh_exec(self.update_quota.format(self.testdir, "500M", "500"))
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spacelimit = list_res[3]
            inodelimit = list_res[5]

            assert update_stat == 0, "update quota failed."
            assert spacelimit == "500MiB"
            assert inodelimit == "500"

            #更新后在次写入数据
            sleep(5)
            touch_stat, _ = self.sshclient.ssh_exec("touch %s/touch{1..50}" % self.testpath)
            assert touch_stat == 0, "touch file failed."

            #5.删除后再次设置,选择不覆盖已有pjid
            del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            assert del_stat == 0, "delete quota failed."
            sleep(2)
            add_again_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "500M", "500"))
            assert add_again_stat == 0, "add quota failed."
            sleep(2)
            #查看list情况
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert spaceused == "0.0B"
            assert inodeused == "0"
            assert list_stat == 0, "list quota failed."

            #6.删除后再次设置，选择覆盖已有pjd
            del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            assert del_stat == 0, "delete quota failed."
            add_again_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "500M", "500"))
            assert add_again_stat == 0, "add quota failed."
            #查看list情况
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert spaceused == "200MiB"
            assert inodeused == "151"
            assert list_stat == 0, "list quota failed."

            #7.rename目录测试
            rename_stat, _ = self.sshserver.ssh_exec("mv {0} {0}new".format(self.testpath))
            assert rename_stat == 0, "rename failed."
            sleep(2)
            list_stat, _ = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "new"))
            assert list_stat == 0, "list verbose failed."
            self.sshserver.ssh_exec("mv {0}new {0}".format(self.testpath))
            sleep(5)

        finally:
            self.sshserver.ssh_exec(self.get_cli("acl_ip_del", self.testdir, "*"))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "new"))

    def test_add_exceed(self):
        '''
        3663 （非空目录quota）文件数量超过quota数值目录设置后无法继续写入
        '''
        #创建测试文件
        try:
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/file1 bs=1M count=200 oflag=direct" % self.testpath)
            self.sshserver.ssh_exec("touch %s/touch{1..20}" % self.testpath)
            #设置quota小于已存在数据量
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "100M", "10"))
            assert add_stat == 0, "add quota failed."
            sleep(5)
            #验证无法写入数据
            touch_stat, _ = self.sshserver.ssh_exec("touch %s/touch21" % self.testpath)
            assert touch_stat != 0, "touch success."
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))

    def test_sixteen_dir(self):
        '''
        3677 （非空目录quota）16层目录设置成功
        '''
        try:
            #创建测试目录
            testpath = self.testpath + "/d2/d3/d4/d5/d6/d7/d8/d9/d10/d11/d12/d13/d14/d15/d16"
            self.sshserver.ssh_exec("mkdir -p " + testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/file1 bs=1M count=100 oflag=direct" % testpath)
            #创建quota目录
            test_subdir = ""
            for i in range(1,17):
                if i == 1:
                    add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "1T", "10000"))
                    assert add_stat == 0, "add quota failed."
                else:
                    test_subdir = test_subdir + "/d" + str(i)
                    add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir + test_subdir, "1T", "10000"))
                    assert add_stat == 0, "add quota failed."
            #检验quota list信息正确性
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0,"list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "17"
        finally:
            for i in range(1,17):
                if i == 1:
                    self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
                else:
                    test_subdir = test_subdir + "/d" + str(i)
                    self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + test_subdir))

    def test_batch_set(self):
        '''
        caseID: 3666 （非空目录quota）批量quota设置成功
        '''
        unit = ("k","m","g","t","p")
        #批量添加quota
        try:
            for i in range(50):
                self.sshserver.ssh_exec("mkdir -p %s/dir%s/file1" % (self.testpath, i))
                testdir = self.testdir + "/dir" + str(i)
                space = str(random.randint(0, 500)) + random.choice(unit)
                inode = random.randint(0, 9999999)
                add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(testdir, space, inode))
                assert add_stat == 0, "add quota failed."
                #检查list是否成功
                list_stat, _ = self.sshserver.ssh_exec(self.quota_verbose.format(testdir))
                assert list_stat == 0, "list quota verbose failed."
        finally:
            #批量删除quota删除操作
            for i in range(50):
                testdir = self.testdir + "/dir" + str(i)
                del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(testdir))
                assert del_stat == 0, "del quota failed."
                list_stat, _ = self.sshserver.ssh_exec(self.quota_verbose.format(testdir))
                assert list_stat != 0, "list quota verbose success."

    #@pytest.mark.skip(msg="skip")
    def test_set_subdir(self):
        '''
        caseID: 3669 （非空目录quota）父目录已设置非空quota，设置子目录非空quota不覆盖已有prjid
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #set 父目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            #set 子目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #检查父目录set used信息是不是正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
            # 检查子目录set used信息是不是正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "0.0B"
            assert inodeused == "0"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))

    def test_set_subdir_ignore(self):
        '''
        caseID: 3669 （非空目录quota）父目录已设置非空quota，设置子目录非空quota覆盖已有prjid
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #set 父目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            #set 子目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #检查父目录set used信息是不是正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
            # 检查子目录set used信息是不是正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "12"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))

    def test_set_parentdir(self):
        '''
        caseID: 3670 （非空目录quota）子目录已存在非空目录设置完成，设置父目录过程中不覆盖子目录成功
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #set 子目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #set 父目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            # 检查子目录set used信息正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "12"
            #检查父目录set used信息是不是正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))

    def test_set_parentdir_ignore(self):
        '''
        caseID: 3671 （非空目录quota）子目录已存在非空目录设置完成，设置父目录过程中覆盖子目录成功
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #set 子目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #set 父目录quota
            sleep(2)
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            # 检查子目录set used信息正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "0.0B"
            assert inodeused == "0"
            #检查父目录set used信息是不是正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))

    def test_quota_nonsubdir(self):
        '''
        3676 （非空目录quota）父目录为正常quota设置非空子目录quota成功
        '''
        try:
            #set 父目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.get_cli("quota_set", self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #set 子目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #检查父目录set used信息是不是正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            recursive = list_res[-4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
            assert recursive == "false","dir Recursive"

            # 检查子目录set used信息是不是正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            recursive = list_res[-4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "12"
            assert recursive == "true", "dir not Recursive"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))

    def test_del_first_dir(self):
        '''
        3681 （非空目录quota）三层目录quota删除最上层quota,其他层显示正确
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/dir1/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #设置第一层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            #设置第二层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #设置第三层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            #删除最一层的quota配置
            sleep(2)
            del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            assert del_stat == 0, "del quota failed"
            #检查第二层目录quota是否正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
            #检查第三层目录quota是否正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "12"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1/dir1"))

    def test_del_third_dir(self):
        '''
        3736 (非空目录quota)三层目录quota删除最低层quota,其他层显示正确。
        '''
        try:
            #创建测试数据
            self.sshserver.ssh_exec("mkdir -p %s/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("mkdir -p %s/dir1/dir1/dir{1..10}" % self.testpath)
            self.sshserver.ssh_exec("dd if=/dev/zero of=%s/dir1/dir1/dir1/file1 bs=1M count=100 oflag=direct" % self.testpath)
            #设置第一层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "10G", "100"))
            assert add_stat == 0,"add quota failed."
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "32"
            #设置第二层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
            #设置第三层目录quota
            add_stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir + "/dir1/dir1", "10G", "100"))
            assert add_stat == 0, "add quota failed."
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "12"
            sleep(2)
            #删除第三层的quota配置
            del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1/dir1"))
            assert del_stat == 0, "del quota failed"
            #检查第一层目录quota是否正确
            sleep(2)
            list_stat,  list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "32"
            #检查第二层目录quota是否正确
            sleep(2)
            list_stat, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir + "/dir1"))
            list_res = list_res_tmp.split("\n")[2].split()
            spaceused = list_res[2]
            inodeused = list_res[4]
            assert list_stat == 0, "list quota failed."
            assert spaceused == "100MiB"
            assert inodeused == "22"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1"))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir + "/dir1/dir1"))

    def test_interupt_del(self):
        '''
        3665 （非空目录quota）设置quota过程中断后删除设置
        '''
        try:
            #创建测试文件10000个。
            self.sshserver.ssh_exec("touch %s/file{1..20000}" % self.testpath)
            #设置quota
            self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "10G", "20000") + " &")
            sleep(1)
            #kill quota设置进程
            self.sshserver.ssh_exec("ps aux|grep \"yrcli --projectquota\"|grep -v grep|awk '{print $2}'|xargs -I "\
                                    "{} kill -9 {}")
            #查询状态
            list_stat, list_res = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            opstatus = list_res.split("\n")[2].split()[7]
            assert list_stat == 0, "list quota failed."
            assert opstatus == "processing", "quota status not processing."
            #删除quota
            del_stat, _ = self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))
            assert del_stat == 0, "delete failed."
            #确认被删除
            list_stat, list_res = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            assert list_stat != 0, "del quota failed"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))

    def test_set_continue(self):
        '''
        3664 （非空目录quota）设置quota过程中断后继续设置成功
        '''
        try:
            #创建测试文件10000个。
            client_mount(self.clientip, acl_add=True)
            self.sshclient.ssh_exec(self.mdtest.format(self.testpath))
            sleep(1)
            #设置quota
            self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "10G", "200000") + " &")
            sleep(5)
            #kill quota设置进程
            self.sshserver.ssh_exec("ps aux|grep \"yrcli --projectquota\"|grep -v grep|awk '{print $2}'|xargs -I "\
                                    "{} kill -9 {}")
            #查询状态
            list_stat, list_res = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            opstatus = list_res.split("\n")[2].split()[7]
            assert list_stat == 0, "list quota failed."
            assert opstatus == "processing", "quota status not processing."
            #continue quota设置
            continue_stat, _ = self.sshserver.ssh_exec(self.get_cli("quota_continue", self.testdir))
            assert continue_stat == 0, "quota set continue failed."
            #确认设置完成
            list_stat, list_res = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            opstatus = list_res.split("\n")[2].split()[7]
            assert list_stat == 0, "list quota failed"
            assert opstatus == "finished", "quota status not finished"
        finally:
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))

    def test_writing_set(self):
        """
        3667 （非空目录quota）数据写入过程中设置成功
        """
        #挂载客户端
        client_mount(self.clientip, acl_add=True)
        #写入数据过程中
        try:
            self.sshclient.ssh_exec(self.mdtest.format(self.testpath) + " &")
            sleep(20)
            #set quota
            addstat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "100G", "200000"))
            assert addstat == 0, "Expect add quota success."
            #查看quota设置正确
            _, list_res_tmp = self.sshserver.ssh_exec(self.quota_verbose.format(self.testdir))
            list_res = list_res_tmp.split("\n")[2].split()
            inodeused = list_res[4]
            assert int(inodeused) > 0, "Expect inode set correct."
        finally:
            self.sshclient.ssh_exec("killall -9 mdtest")
            self.sshserver.ssh_exec("mkdir -p {0};rsync -apgolr --delete {0} {1}/".format("/autotest_rsync/", self.testpath))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))

    def test_set_child(self):
        """
        3668 （非空目录quota）父目录设置非空quota过程中，设置子目录非空成功
        """
        # 创建测试文件
        subdir = self.testdir + "/dir1"
        subpath = self.testpath + "/dir1"
        try:
            self.sshserver.ssh_exec("mkdir -p " + subpath)
            self.sshserver.ssh_exec("touch %s/file{1..2000}" % subpath)
            #set parent dir quota
            self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "200M", "5000") + " &")
            #set child dir quota
            sleep(1)
            stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(subdir, "200M", "5000"))
            assert stat == 0, "Expect add quota success."
        finally:
            self.sshserver.ssh_exec("ps axu|grep projectquota|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
            self.sshserver.ssh_exec(self.delete_quota.format(subdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))

    @pytest.mark.parametrize("mode", ("recov", "norecov"))
    def test_recover_parent(self, mode):
        """
        3673 （非空目录quota）子目录已存在非空目录设置中，选择覆盖该目录父目录设置成功。
        """
        subdir = self.testdir + "/dir1"
        subpath = self.testpath + "/dir1"
        try:
            #创建测试文件
            self.sshserver.ssh_exec("mkdir -p " + subpath)
            self.sshserver.ssh_exec("touch %s/file{1..5000}" % subpath)
            #set subdir quota
            self.sshserver.ssh_exec(self.add_quota.format(subdir, "200G", "500000") + " &")
            sleep(5)
            if mode == "norecov":
                stat, _ = self.sshserver.ssh_exec(self.add_quota.format(self.testdir, "200G", "500000"))
            else:
                stat, _ = self.sshserver.ssh_exec(self.add_ignore_quota.format(self.testdir, "200G", "500000"))

            assert stat == 0, "Expect: set parent dir quota success"
        finally:
            self.sshserver.ssh_exec("ps axu|grep projectquota|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
            self.sshserver.ssh_exec(self.delete_quota.format(subdir))
            self.sshserver.ssh_exec(self.delete_quota.format(self.testdir))