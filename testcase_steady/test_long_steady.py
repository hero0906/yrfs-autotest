#coding=utf-8

import pytest
from common.fault import makeFault

@pytest.mark.steadyTest
class Test_longsteady():
    def setup(self):
        self.makefault = makeFault()

    def test_kill_meta(self):
        '''
        kill meta master故障测试
        '''
        self.makefault.kill_meta()

    @pytest.mark.skip
    def test_reboot_meta(self):
        '''
        reboot meata 故障测试
        '''
        self.makefault.reboot_meta()

    def test_kill_oss(self):
        '''
        双oss 服务故障测试
        '''
        self.makefault.kill_oss()

    @pytest.mark.skip
    def test_reboot_mgr(self):
        '''
        mgr master node reboot故障测试。
        '''
        self.makefault.reboot_mgr()

    def test_kill_mgr(self):
        '''
        kill mgr master service故障测试
        '''
        self.makefault.kill_mgr()

    def test_down_mgr(self):
        '''
        down mgr存储网卡故障测试
        '''
        self.makefault.down_mgr()