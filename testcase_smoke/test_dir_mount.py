#coding=utf-8

'''
@Desciption : test sub dir mount
@Time : 2020/10/20 18:58
@Author : caoyi
'''

import pytest
import os
from common.cli import YrfsCli
from config import consts
from common.util import ssh_exec,read_config,ip6_Prefix
from depend.skip_mark import verify_mount_point
from common.cluster import get_client_storageip

client = consts.CLIENT[0]
ip = consts.META1
conf = read_config('test_dir_mount')

@pytest.fixture(scope='module', params=conf)
def data_init(request):
    param = request.param
    ssh_exec(ip, "mkdir -p %s" % (os.path.join(consts.MOUNT_DIR, param['path'])))
    yield param
    ssh_exec(ip, "rm -fr %s" % (os.path.join(consts.MOUNT_DIR, param['path'])))

#@pytest.mark.skipif(verify_mount_point() != 0, reason="server yrfs mount point not exist")
@pytest.mark.smokeTest
class Test_dir_mount(YrfsCli):

    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="skip,server yrfs mount point not exist", allow_module_level=True)
        self.client_storageip = get_client_storageip(client)

    def test_acl_ip4_add(self, data_init):
        '''
        caseID:1998 ip访问方式添加目录acl
        '''
        cmd = self.get_cli('acl_ip_add', data_init['path'], self.client_storageip, data_init['mode'])
        res = ssh_exec(ip, cmd)
        assert data_init['succ_result'] in res

    def test_acl_id_add(self, data_init):
        '''
        caseID:3037 id访问方式添加目录acl
        '''
        cmd = self.get_cli('acl_id_add', data_init['path'], data_init['id'], data_init['mode'])
        res = ssh_exec(ip, cmd)
        assert data_init['succ_result'] in res

    #@pytest.mark.skip()
    def test_acl_ip4_mount(self, data_init):
        '''
        客户端acl ip4挂载
        '''
        ssh_exec(client, "/etc/init.d/yrfs-client stop")
        cmd = self.get_cli('oss_node') + "|grep IPv4 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|awk -F '<'\
         '{print $2}'|uniq|head -n 3"
        mgmt_ip4_tmp = ssh_exec(ip, cmd).split("\n")
        mgmt_ip4 = ",".join(mgmt_ip4_tmp)
        #获取yrfs-cient.conf
        ssh_exec(client, 'echo "cluster_addr = %s" > %s' % (mgmt_ip4, consts.CLIENT_CONFIG))
        #配置yrfs-client.config配置文件
        ssh_exec(client, "echo -e \"/mnt/{path} {config} /{path}\" > {mount_file}".format(path=data_init['path'],config=consts.CLIENT_CONFIG,mount_file=consts.CLIENT_MOUNT_FILE))
        ssh_exec(client, "systemctl start yrfs-client")
        #配置net文件
        net_config = ssh_exec(ip, "cat " + consts.CLIENT_NET_FILE)
        ssh_exec(client, "echo \"%s\" > %s" % (net_config, consts.CLIENT_NET_FILE))
        #验证客户端挂载点是否存在
        ssh_exec(client, "/etc/init.d/yrfs-client start")
        findmnt = ssh_exec(client, "findmnt /mnt/{path}".format(path=data_init['path']))
        assert "/mnt/" + data_init['path'] in findmnt

        res = ssh_exec(client, "dd if=/dev/zero of=/mnt/{path}/{path} bs=1M count=5".format(path=data_init['path']))
        assert "copied" in res

    #@pytest.mark.skip()
    def test_ip4_id_mount(self, data_init):
        '''
        客户端 ip4 id方式挂载
        '''
        ssh_exec(client, "/etc/init.d/yrfs-client stop")
        #获取其他节点yrfs-cient.conf
        cmd = self.get_cli('oss_node') + "|grep IPv4 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|awk -F '<'\
         '{print $2}'|uniq|head -n 3"
        mgmt_ip4_tmp = ssh_exec(ip, cmd).split("\n")
        mgmt_ip4 = ",".join(mgmt_ip4_tmp)
        #获取yrfs-cient.conf
        ssh_exec(client, 'echo "cluster_addr = %s" > %s' % (mgmt_ip4, consts.CLIENT_CONFIG))

        ssh_exec(client, "echo -e \"/mnt/{path} {config} /{path} {Id}\" > {mount_file}".format(path=data_init['path'],\
             config=consts.CLIENT_CONFIG,Id=data_init['id'],mount_file=consts.CLIENT_MOUNT_FILE))
        ssh_exec(client, "/etc/init.d/yrfs-client start")

        #配置net文件
        net_config = ssh_exec(ip, "cat " + consts.CLIENT_NET_FILE)
        ssh_exec(client, "echo \"%s\" > %s" % (net_config, consts.CLIENT_NET_FILE))
        #验证mount挂载点是否成功
        findmnt = ssh_exec(client, "findmnt /mnt/{path}".format(path=data_init['path']))
        assert "/mnt/" + data_init['path'] in findmnt

        res = ssh_exec(client, "dd if=/dev/zero of=/mnt/{path}/{path} bs=1M count=5".format(path=data_init['path']))
        #res = ssh_exec(client, "/etc/init.d/yrfs-client status")
        assert "copied" in res

    @pytest.mark.skip("config change.")
    def test_ip6_id_mount(self, data_init):
        '''
        caseID：3101 client ip6 id方式挂载测试
        '''
        ssh_exec(client, "/etc/init.d/yrfs-client stop")
        cmd = self.get_cli('oss_node') + "|grep IPv6 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|awk -F '<' '{print $2}'|uniq|head -n 3"
        mgmt_ip6_tmp = ssh_exec(ip, cmd).split("\n")
        mgmt_ip6s = ",".join(mgmt_ip6_tmp)
        #写入ip6地址到client配置文件
        ssh_exec(client, 'echo -e "mgmtd_hosts = %s" > %s' % (mgmt_ip6s, consts.CLIENT_CONFIG))
        #获取ip6 address前缀
        prefix = ip6_Prefix(mgmt_ip6_tmp[0])
        # 写入net文件
        ssh_exec(client, 'echo "%s" > %s' % (prefix, consts.CLIENT_NET_FILE))
        #写入挂载目录到mounts配置文件
        ssh_exec(client, "echo -e \"/mnt/{path} {config} /{path} {Id}\" > {mount_file}".format(path=data_init['path'],\
        config=consts.CLIENT_CONFIG,Id=data_init['id'],mount_file=consts.CLIENT_MOUNT_FILE))

        ssh_exec(client, "/etc/init.d/yrfs-client start")
        findmnt = ssh_exec(client, "findmnt /mnt/{path}".format(path=data_init['path']))
        assert "/mnt/" + data_init['path'] in findmnt

        res = ssh_exec(client, "dd if=/dev/zero of=/mnt/{path}/{path} bs=1M count=5".format(path=data_init['path']))
        assert "copied" in res

    #@pytest.mark.skip()
    def  test_acl_list(self, data_init):
        '''
        caseID:2008 列出目录acl
        '''
        cmd = self.get_cli('acl_list')
        res = ssh_exec(ip, cmd)
        assert data_init['path'] and data_init['mode'] in res

    #@pytest.mark.skip()
    def test_acl_ip_del(self, data_init):
        '''
        caseID:2014 删除目录ip acl
        '''
        cmd = self.get_cli('acl_ip_del', data_init['path'], self.client_storageip)
        res = ssh_exec(ip, cmd)
        assert data_init['succ_result'] in res

    #@pytest.mark.skip()
    def test_acl_id_del(self, data_init):
        '''
        caseID:3037 删除目录id acl
        '''
        cmd = self.get_cli('acl_id_del', data_init['path'], data_init['id'])
        res = ssh_exec(ip, cmd)
        del_dir = ssh_exec(ip, "rm -fr {mount_point}/{path}/{path}".format(mount_point=consts.MOUNT_DIR,path=data_init['path']))
        assert data_init['succ_result'] in res