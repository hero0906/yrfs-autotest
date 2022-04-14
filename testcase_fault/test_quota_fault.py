# coding=utf-8

'''
@Desciption : quota dir function case
@Time : 2021/07/28 
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
from common.cluster import get_mds_master, get_osd_master, check_cluster_health

logger = logging.getLogger(__name__)

server = consts.META1
client1 = consts.CLIENT[0]
conf = read_config('test_quota_func')

@pytest.fixture(scope="class", params=conf)
def data_init(request):
    param = request.param
    yield param


#pytest.mark.skipif(verify_mount_point() != 0, reason="server yrfs mount point not exist")
@pytest.mark.faultTest
class Test_QuotaFunc_Fault(YrfsCli):
    '''
    quota的容错能力测试
    '''

    def setup_class(self):
        if verify_mount_point() !=0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)

        self.space = "10G"
        self.inode = 5000

        self.mount_subdir = "mount_subdir"
        self.quota_dir = "quota_dir"

        # Client侧的完整路径: /mnt/yrfs/quota_dir
        self.client_fulldir = os.path.join(consts.MOUNT_DIR, self.quota_dir)

        # Server侧提供的挂载点的完整路径：/mnt/yrfs/mount_subdir
        self.server_fulldir_mount = os.path.join(consts.MOUNT_DIR, self.mount_subdir)

        # Server侧, CLI命令中使用的路径, 并不包含/mnt/yrfs/
        self.cli_quota_dir = os.path.join(self.mount_subdir, self.quota_dir)

    def setup(self):
        sshServer = sshClient(server)    
        sshclient1= sshClient(client1)          
        sleep(1)

        ssh_exec(server, "rm -fr %s*" % (self.server_fulldir_mount))
        ssh_exec(server, "mkdir -p %s" %(self.server_fulldir_mount))      
        cmd = self.get_cli("acl_ip_add", self.mount_subdir, "*", "rw")
        sshServer.ssh_exec(cmd)           
        ssh_exec(server, "cd %s; mkdir %s" %(self.server_fulldir_mount,self.quota_dir))  
        
        #到client上去挂载目录
        mstat = client_mount(client1, self.mount_subdir)
        assert mstat == 0, "Client mount failed."
        sshServer.ssh_exec(self.get_cli("quota_remove", self.mount_subdir))
        sshServer.ssh_exec(self.get_cli('quota_set', self.cli_quota_dir, self.space, self.inode))
        sshServer.ssh_exec(self.get_cli('quota_list'))        
        sshServer.close_connect()
        sshclient1.close_connect()        
        
        sleep(1)


    def teardown(self):
        sleep(1)
        cmd = self.get_cli("acl_ip_del", self.mount_subdir, "*")
        ssh_exec(server, cmd)
        ssh_exec(server, self.get_cli("quota_remove", self.mount_subdir))
        ssh_exec(server, "rm -fr %s*" % (self.server_fulldir_mount))

        
    def test_rename_quotadir_iperf(self):
        '''
        3019 quota目录数据写入，节点网络带宽占满
        '''
        #ifconfig | grep broadcast | grep -v 192 | awk '{print $2}'
        sshclient1= sshClient(client1)   
         
        #第一次写入配额的80%, 并找到该目录的mds。
        cmd = "dd if=/dev/zero of=%s/testfile1 bs=1M count=8000 " % (self.client_fulldir)
        stat1, res1 = sshclient1.ssh_exec(cmd )
                             
        #找到该目录的归属mds的IP地址    
        _, master_mds_node = get_mds_master("mount_subdir/quota_dir/testfile1")
        logger.info("master_mds_node: %s." % (master_mds_node))
        sshMds = sshClient(master_mds_node)
        stat, resip = sshMds.ssh_exec(" ifconfig | grep broadcast | grep -v 192 | awk '{print $2}' ")
        logger.info("IP: %s." % (resip))
        
        #异步执行iperf，预计持续30秒到60秒
        sshMds.ssh_exec(" iperf -u -c %s -b 5000M -i 1 -w 1M -t 30 &" %(resip))
        
        #第二次再写入配额的80%, 预期失败       
        cmd = "dd if=/dev/zero of=%s/testfile2 bs=1M count=8000" % (self.client_fulldir)
        stat2, res2 = sshclient1.ssh_exec(cmd)
        logger.info("dd write: %s." % (res2))
        #删除测试目录
        sleep(30)
        #sshclient1.ssh_exec("rm -fr %s" % (self.client_fulldir))
        sshMds.close_connect()
        sshclient1.close_connect()        
        
        #验证结果的正确性        
        assert stat1 == 0, "dd(1) write should OK, but fail" 
        assert stat2 == 1, "dd(2) write should permit,but OK"


    def test_rename_quotadir_fault_mds(self):
        '''
        3020 quota目录数据写入过程中，mds故障，不应影响配额统计
        '''   
        sshclient1= sshClient(client1)   
        
        #第一次写，预期成功，同时为了找到指定的mds
        cmd = "dd if=/dev/zero of=%s/testfile1 bs=1M count=8000" % (self.client_fulldir) 
        stat1, res1 = sshclient1.ssh_exec(cmd )
             
        #找到该目录的归属mds'             
        _, master_mds_node = get_mds_master("mount_subdir/quota_dir/testfile1")
        logger.info("master_mds_node: %s." % (master_mds_node))
        sshMds = sshClient(master_mds_node) 
        
        #kill掉全体mds，然后又重新拉起
        logger.info("Kill mds Begin ------ " )
        sshMds.ssh_exec("ps axu|grep yrfs-mds |grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
        sleep(1)        
        sshMds.ssh_exec("systemctl restart yrfs-mds@mds0")  
        sshMds.ssh_exec("systemctl restart yrfs-mds@mds1") 
        logger.info("Restart mds End ------" )  
        # 不要sleep，立即写        
   
        #第二次，大量写，预期写入失败       
        cmd = "dd if=/dev/zero of=%s/testfile2 bs=1M count=8000" % (self.client_fulldir) 
        stat2, res2 = sshclient1.ssh_exec(cmd)
        logger.info("dd write: %s." % (res2))
        #删除测试目录
        sshclient1.ssh_exec("rm -fr %s" % (self.client_fulldir))
        sshclient1.close_connect()
        # 检查集群健康状态
        check_cluster_health()
        #验证结果的正确性        
        assert stat1 == 0, "dd write should be OK, but fail" 
        assert stat2 == 1, "dd write should be refused, but OK"
        

    def test_rename_quotadir_fault_osd(self):
        '''
        3021 quota目录数据写入过程中，storage节点故障配额统计
        '''
        sshclient1= sshClient(client1)
        #第一次写入配额的80%，
        cmd = "dd if=/dev/zero of=%s/testfile1 bs=1M count=8000" % (self.client_fulldir) 
        stat1, res1 = sshclient1.ssh_exec(cmd )
                
        master_oss_node = get_osd_master("mount_subdir/quota_dir/testfile1")[0]
        logger.info("master_oss_node: %s." % (master_oss_node))
        sshOss = sshClient(master_oss_node) 
        
        #Kill掉OSS，然后重新拉起
        logger.info("Kill Oss Begin ------ " )
        sshOss.ssh_exec("ps axu | grep yrfs-oss | grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
        sleep(1)
        sshOss.ssh_exec("systemctl restart yrfs-oss") 
        logger.info("Restart Oss End ------ " )        
        #不要sleep，立即写               
             
        #第二次再写入配额的80%, 预期失败       
        cmd = "dd if=/dev/zero of=%s/testfile2 bs=1M count=8000" % (self.client_fulldir) 
        stat2, res2 = sshclient1.ssh_exec(cmd)
        logger.info("dd write: %s." % (res2))        
        
        #删除测试目录
        sshclient1.ssh_exec("rm -fr %s" % (self.client_fulldir))
        sshOss.close_connect()
        sshclient1.close_connect()
        #检查集群健康状态
        check_cluster_health()
        #验证结果的正确性        
        assert stat1 == 0, "dd(1) write should OK, but fail" 
        assert stat2 == 1, "dd(2) write should permit,but OK"