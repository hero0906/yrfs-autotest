# coding=utf-8

'''
@Desciption : quota dir function case
@Time : 2021/07/28 18:58
@Author : zhangqi
'''

import os
import pytest
from time import sleep
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec, sshClient, read_config
from depend.skip_mark import verify_mount_point
from common.log import logging
from depend.client import client_mount

logger = logging.getLogger(__name__)

server = consts.META1
client1 = consts.CLIENT[0]


@pytest.mark.funcTest
class Test_QuotaFunc(YrfsCli):
    '''
    单节点quota功能测试,
    '''
    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)

        self.space = "2048M"
        self.inode = 10

        self.mount_subdir = "autotest_mount_subdir"
        self.quota_dir = "quota_dir"

        # Client侧的完整路径: /mnt/yrfs/quota_dir
        self.client_fulldir = os.path.join(consts.MOUNT_DIR, self.quota_dir)

        # Server侧提供的挂载点的完整路径：/mnt/yrfs/mount_subdir
        self.server_fulldir_mount = os.path.join(consts.MOUNT_DIR, self.mount_subdir)

        # Server侧, CLI命令中使用的路径, 并不包含/mnt/yrfs/
        self.cli_quota_dir = os.path.join(self.mount_subdir, self.quota_dir)
        
    
    def setup(self):
        sshServer = sshClient(server)
        sleep(1)

        ssh_exec(server, "rm -fr %s*" % (self.server_fulldir_mount))
        ssh_exec(server, "mkdir -p %s" %(self.server_fulldir_mount))
        #设置acl
        cmd = self.get_cli("acl_ip_add", self.mount_subdir, "*", "rw")
        sshServer.ssh_exec(cmd)           
        ssh_exec(server, "cd %s; mkdir %s" %(self.server_fulldir_mount,self.quota_dir))  

        #客户端挂载子目录
        mount_stat = client_mount(client1, self.mount_subdir)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed. skip.", allow_module_level=True)

        sshServer.ssh_exec(self.get_cli('quota_set', self.cli_quota_dir, self.space, self.inode))
        sshServer.ssh_exec(self.get_cli('quota_list'))        
        sshServer.close_connect()

    def teardown(self):
        cmd = self.get_cli("acl_ip_del", self.mount_subdir, "*")
        ssh_exec(server, cmd);
        ssh_exec(server, "rm -fr %s*" % (self.server_fulldir_mount))

    def test_rename_quotadir_sla(self):
        '''
        caseID: XXXX 设置quota后重命名该目录sla_info被更新
        '''
        sshServer = sshClient(server)    
        sshclient1= sshClient(client1)   
  

        # 写文件，然后才会触发sla信息
        cmd = "dd if=/dev/zero of=%s/test-1000M bs=1M count=1000 oflag=direct" % (self.client_fulldir)
        ssh_exec(client1, cmd )
     
        #通过mv命令修改目录名
        quota_dir02 = self.quota_dir + "02"
        stat1, res1 = sshclient1.ssh_exec("cd %s;  mv %s %s; " %(consts.MOUNT_DIR, self.quota_dir, quota_dir02 ))
        sleep(1)
        
        #看sla是否已经更新（包含新目录名）
        stat1, res1 = sshclient1.ssh_exec("cat /proc/fs/yrfs/*yrfs*/sla_info | grep %s " %(quota_dir02))   
     
        #删除测试目录
        sleep(1)
        sshclient1.ssh_exec("rm -fr %s" % (self.client_fulldir))
        sshServer.close_connect()
        sshclient1.close_connect()        
        
        #验证结果的正确性
        assert stat1 == 0, "slainfo has already changed"





