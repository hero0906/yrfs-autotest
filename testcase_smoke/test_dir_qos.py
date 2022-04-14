# coding=utf-8

'''
@Desciption : qos dir test
@Time : 2020/10/22 10:31
@Author : caoyi
'''

import pytest
import os
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec,read_config,sshClient
from time import sleep
from depend.skip_mark import verify_mount_point

serverip = consts.META1
conf = read_config('test_dir_qos')

@pytest.fixture(scope='class', params=conf)
def data_init(request):
    param = request.param
    ssh_exec(serverip, "mkdir %s" % (os.path.join(consts.MOUNT_DIR, param['path'])))
    yield param
    ssh_exec(serverip, "rm -fr %s" % (os.path.join(consts.MOUNT_DIR, param['path'])))

@pytest.mark.smokeTest
class Test_dir_qos(YrfsCli):

    def setup_class(self):
        if verify_mount_point() !=0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)
        self.sshserver = sshClient(serverip)

    def teardown_class(self):
        self.sshserver.close_connect()

    #@pytest.mark.usefixtures('initdir')
    def test_qos_total_set(self, data_init):
        '''
        caseID: 3065 qos总值设置验证
        '''
        set_qos_cmd = self.get_cli('qos_total_set', data_init['path'], data_init['bps'], data_init['iops'], data_init['mops'])
        qos_stat, _ = self.sshserver.ssh_exec(set_qos_cmd)
        assert qos_stat == 0, "qos set failed."
    
    def test_qos_part_set(self, data_init):
        '''
        caseID: 3065 qos分值设置验证 
        '''
        cmd = self.get_cli('qos_part_set', data_init['path'], data_init['bps'], data_init['bps'], data_init['iops'], data_init['iops'], data_init['mops'])
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat == 0

    def test_part_set_limit(self, data_init):
        '''
        caseID: 3092 qos限制的准确性
        '''
        #验证dd写入速度与qos限制是否相符
        sleep(10)
        _, dd_res = self.sshserver.ssh_exec("dd if=/dev/zero of=%s/%s bs=1M count=20" % (os.path.join(consts.MOUNT_DIR, data_init['path']), data_init['path']))
        assert data_init['bps'][0] == dd_res.split(',')[-1][1]
     
    def test_qos_single_set(self, data_init):
        '''
        caseID: 3064 qos单独设置验证
        '''
        cmd = self.get_cli('qos_single_set', data_init['path'], "riops", data_init['iops'])
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat == 0

    def test_qos_error_param(self, data_init):
        '''
        caseID: 3066 设置参数为负数时报错
        '''
        cmd = self.get_cli('qos_total_set', data_init['path'], data_init['bps'], data_init['invalid_param'], data_init['mops'])
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat != 0,"qos set succes."

    
    def test_qos_list(self, data_init):
        '''
        caseID: 3069 查询qos设置
        '''
        cmd = self.get_cli('qos_list') + '|grep ' + data_init['path']
        stat, res = self.sshserver.ssh_exec(cmd)
        assert data_init['path'] and str(data_init['iops']) in res

    def test_sixteen_qos_dir(self, data_init):
        '''
        caseID: 3138 验证qos目录设置最高上限为16层
        '''
        sleep(5)
        subdir1 = data_init['path'] + '/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14/dir15/dir16'
        subdir2 = data_init['path'] + '/dir2/dir3/dir4/dir5/dir6/dir7/dir8/dir9/dir10/dir11/dir12/dir13/dir14/dir15/dir16/dir17'

        self.sshserver.ssh_exec('mkdir -p ' + os.path.join(consts.MOUNT_DIR, subdir1))
        self.sshserver.ssh_exec('mkdir -p ' + os.path.join(consts.MOUNT_DIR, subdir2))
        sleep(5)
        stat1, res1 = self.sshserver.ssh_exec(self.get_cli('qos_single_set', subdir1, 'riops', data_init['iops']))
        stat2, res2 = self.sshserver.ssh_exec(self.get_cli('qos_single_set', subdir2, 'wiops', data_init['iops']))

        sleep(5)
        assert stat1 == 0
        assert stat2 != 0

    def test_qos_remove(self, data_init):
        '''
        caseID: 3068 删除目录qos
        '''
        cmd = self.get_cli('qos_remove', data_init['path'])
        stat, res = self.sshserver.ssh_exec(cmd)
        assert stat == 0,"remove qos failed."