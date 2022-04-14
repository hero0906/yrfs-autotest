# coding=utf-8
'''
@Desciption : quota dir 5120 update.
@Time : 2021/03/23 14:44
@Author : caoyi
'''

import pytest
import os
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from time import sleep

#@pytest.mark.skip(reason="expect skip, this case test time too long.")
@pytest.mark.faultTest
class TestquotaUpperlimit(YrfsCli):
    '''
    quota目录到达5120后，update成功
    '''
    serverip = consts.META1
    def test_update_5120(self):
        '''
        bugID:  3955 【6.5.4】【quota】quota目录超过5120上限后，update已有设置不成功。
        '''

        try:
            sshserver = sshClient(self.serverip)
            # 检查集群已有quota数量：
            _, res = sshserver.ssh_exec(self.get_cli("quota_list") + "|awk 'NR >3'|wc -l")
            nums = 5121-int(res)
            #开始创建quota
            for num in range(1, nums):
                testdir = "autotest/dir%s" % str(num)
                sshserver.ssh_exec("mkdir -p %s" % os.path.join(consts.MOUNT_DIR,testdir))
                quota_cmd = self.get_cli("quota_set",testdir,"20T","100000")
                quota_set_stat, _ = sshserver.ssh_exec(quota_cmd)
                assert quota_set_stat == 0, "expected result, quota set success."
                #sleep(0.1)
            sleep(5)
            quota_cmd = self.get_cli("quota_update",testdir,"100T","999999")
            quota_update_stat, _ = sshserver.ssh_exec(quota_cmd)
            assert quota_update_stat == 0, "expected result, 5120 dir update success."
            sleep(5)
        finally:
            sshserver.ssh_exec("rm -fr %s" % os.path.join(consts.MOUNT_DIR,"autotest"))
            sshserver.close_connect()
            sleep(5)