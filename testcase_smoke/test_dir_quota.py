# coding=utf-8

"""
@Desciption : quota dir test
@Time : 2020/10/20 18:58
@Author : caoyi
"""

import pytest
from time import sleep
import os
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec, read_config, sshClient
from depend.skip_mark import verify_mount_point

ip = consts.META1
conf = read_config('test_dir_quota')


@pytest.fixture(scope="class", params=conf)
def data_init(request):
    param = request.param
    ssh_exec(ip, "mkdir -p %s" % (os.path.join(consts.MOUNT_DIR, param["path"])))
    yield param
    ssh_exec(ip, "rm -fr %s" % (os.path.join(consts.MOUNT_DIR, param["path"])))


@pytest.mark.smokeTest
class Test_dir_quota(YrfsCli):

    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)
        self.sshserver = sshClient(ip)

    def teardown_class(self):
        self.sshserver.close_connect()

    # @pytest.mark.usefixtures('initdir')
    def test_quota_root(self, data_init):
        '''
        caseID: 3027 设置根目录quota不成功
        '''
        sleep(5)
        cmd = self.get_cli('quota_set', '', data_init['space'], data_init['inode'])
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat != 0, "set / quota failed."

    def test_inode_set(self, data_init):
        '''
        caseID:2984 验证单独设置inode限制
        '''
        sleep(5)
        cmd = self.get_cli('quota_inode_set', data_init['path'], '1000')
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "set inode success."

    def test_inode_update(self, data_init):
        '''
        caseID: 2983 更新inode设置
        '''
        sleep(5)
        cmd = self.get_cli('quota_inode_update', data_init['path'], '2000')
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "update inode success."

    def test_list_verbose(self, data_init):
        '''
        caseID:3141 验证quota分开显示子文件和子目录的数量信息正确
        '''
        sleep(5)
        dirnum = 20
        filenum = 30
        # 创建测试文件
        testpath = os.path.join(consts.MOUNT_DIR, data_init['path'])
        self.sshserver.ssh_exec("mkdir %s/dir{1..%s}" % (testpath, dirnum))
        self.sshserver.ssh_exec("touch %s/file{1..%s}" % (testpath, filenum))
        sleep(5)
        # 查询dirused and fileused信息是否正确
        verbose_cmd = self.get_cli('quota_list_verbose', data_init['path'])
        _, res_v = self.sshserver.ssh_exec(verbose_cmd)
        res_list = res_v.split("\n")[2].split()
        # 判断第十列和十一列为dirused和fileused
        dirnum_fact = int(res_list[9])
        filenum_fact = int(res_list[10])
        # 比对实际file dir used与写入数据是否一致，设计时统计数量加上了自身的数量。
        assert dirnum == dirnum_fact - 1, 'quota used目录数量与实际不符'
        assert filenum == filenum_fact, 'quota used文件数量与实际不符'

    def test_inode_del(self, data_init):
        sleep(5)
        cmd = self.get_cli('quota_remove', data_init['path'])
        # 取消quota设置前先删除文件
        rm = "rm -fr %s/*" % (os.path.join(consts.MOUNT_DIR, data_init["path"]))
        rmstat, _ = self.sshserver.ssh_exec(rm)
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert rmstat == 0, "remove file success."
        assert stat == 0, "remove inode success."

    def test_space_set(self, data_init):
        '''
        caseID:2985 验证单独设置space限制
        '''
        sleep(5)
        cmd = self.get_cli('quota_space_set', data_init['path'], '10G')
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "set space success."

    def test_space_update(self, data_init):
        '''
        caseID:2985 验证更新space设置
        '''
        sleep(5)
        cmd = self.get_cli('quota_space_update', data_init['path'], '100G')
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "update space success."

    def test_space_del(self, data_init):
        '''
        caseID:2985 删除space设置
        '''
        sleep(5)
        cmd = self.get_cli('quota_remove', data_init['path'])
        rm = "rm -fr %s" % (os.path.join(consts.MOUNT_DIR, data_init["path"]))
        stat, _ = self.sshserver.ssh_exec(cmd)
        rmstat, _ = self.sshserver.ssh_exec(rm)
        assert stat == 0, "remove space success."
        assert rmstat == 0, "remove file success."

    def test_quota_set(self, data_init):
        '''
        caseID: 2989 quota inode space同时设置验证
        '''
        sleep(5)
        self.sshserver.ssh_exec("mkdir -p " + os.path.join(consts.MOUNT_DIR, data_init["path"]))
        cmd = self.get_cli('quota_set', data_init['path'], data_init['space'], data_init['inode'])
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "set quota success."

    def test_quota_list(self, data_init):
        '''
        caseID: 2986 查询quota设置测试
        '''
        cmd = self.get_cli('quota_list') + "|grep " + data_init['path']
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "list quota success."

    def test_space_limit(self, data_init):
        '''
        caseID: 3002 quota space上限测试
        '''
        count = data_init['space'][:-1]
        sleep(5)
        dd = "dd if=/dev/zero of=%s bs=1M count=%s oflag=direct" % (os.path.join(consts.MOUNT_DIR, data_init['path'],
                                                                                 data_init['path']), int(count) * 2)
        _, res1 = self.sshserver.ssh_exec(dd)
        sleep(10)
        dd = "dd if=/dev/zero of=%s bs=1M count=%s oflag=direct" % (os.path.join(consts.MOUNT_DIR, data_init['path'],
                                                                                 data_init['path'] + data_init[
                                                                                     'space']), count)
        _, res2 = self.sshserver.ssh_exec(dd)

        assert "copied" in res1
        assert "Disk quota exceeded" in res2

    def test_quota_recover(self, data_init):
        '''
        caseID: 3003 quota目录达到上限后，回收测试。
        '''
        # 清除目录空间,quota是否正确收回
        sleep(5)
        count = data_init['space'][:-1]
        del_file = "rm -fr %s/*" % os.path.join(consts.MOUNT_DIR, data_init['path'])
        self.sshserver.ssh_exec(del_file)
        sleep(5)
        dd = "dd if=/dev/zero of=%s bs=1M count=%s oflag=direct" % (os.path.join(consts.MOUNT_DIR, data_init['path'],
                                                                                 data_init['path']), int(count) // 10)
        stat, res = self.sshserver.ssh_exec(dd)
        assert data_init["limit_error_result"] not in res

    def test_inode_limit(self, data_init):
        '''
        caseID: 3000 inode quota上限测试
        '''
        sleep(5)
        touch_cmd = "touch %s/{1..%s}" % (os.path.join(consts.MOUNT_DIR, data_init['path']), data_init['inode'])
        self.sshserver.ssh_exec(touch_cmd)
        sleep(5)
        stat, _ = self.sshserver.ssh_exec(
            "touch %s/%s" % (os.path.join(consts.MOUNT_DIR, data_init['path']), data_init['inode'] * 2))
        assert stat != 0, 'inode touch failed.'

    def test_quota_update(self, data_init):
        '''
        caseID: 2987 inode space更新目录配额
        '''
        sleep(5)
        cmd = self.get_cli('quota_update', data_init['path'], data_init['new_space'], data_init['new_inode'])
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, 'update quota failed.'

    def test_quota_remove(self, data_init):
        '''
        caseID: 2988 删除目录quota成功
        '''
        sleep(5)
        cmd = self.get_cli('quota_remove', data_init['path'])
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat == 0, "remove quota failed."

    def test_nonempty_set(self, data_init):
        '''
        caseID: 3007非空目录设置quota失败
        '''
        # 设置非空目录quota
        sleep(5)
        cmd = self.get_cli('quota_set', data_init['path'], data_init['new_space'], data_init['new_inode'])
        stat, _ = self.sshserver.ssh_exec(cmd)
        assert stat != 0, 'none empty dir set quota success.'
