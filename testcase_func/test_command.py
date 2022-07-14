# coding=utf-8
'''
@Desciption : yrcli command test
@Time : 2022/05/27 10:27
@Author : caoyi
'''

import time
import os
import pytest
import logging
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import consts
from common.util import sshClient
from common.client import client_mount
from common.cluster import get_client_storageip

logger = logging.getLogger(__name__)

@pytest.mark.funcTest
class TestyrfsCommand():
    """
    命令行测试合集
    """
    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.CLUSTER_VIP
        self.testdir = "autotest-command" + time.strftime("%m-%d-%H%M%S")
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        self.mdtest = "timeout 5 mdtest -C -d {0} -i 1 -w 10 -I 8000 -z 0 -b 0 -L -F"

    def setup(self):
        self.sshserver = sshClient(self.serverip)
        self.sshclient = sshClient(self.clientip)
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)

    def teardown(self):
        self.sshserver.ssh_exec("rm -fr " + self.testpath)
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    @pytest.mark.parametrize("TYPE",("oss","mds"))
    def test_iostat(self, TYPE):
        """
        yrcli --iostat 集群ops监控
        """
        #获取客户端存储ip
        stor_ip = get_client_storageip(self.clientip)
        iostat_cmd = "timeout 5 yrcli --iostat --interval=1 --type=%s --filter=%s --maxlines=10" % (TYPE, stor_ip)
        #客户端挂载
        stat = client_mount(self.clientip, acl_add=True)
        assert stat == 0, "client mount failed"
        #同时执行业务观测集群的iostat状态
        pools = []
        pool = ThreadPoolExecutor(max_workers=2)

        p1 = pool.submit(self.sshclient.ssh_exec, self.mdtest.format(self.testpath))
        p2 = pool.submit(self.sshserver.ssh_exec, iostat_cmd)
        #p3 = pool.submit(self.sshserver.ssh_exec, iostat_cmd.format("mds"))
        pools.append(p1)
        pools.append(p2)
        #pools.append(p3)

        for t in as_completed(pools):
            t.result()
        #验证结果中是否存在关键字
        res = p2.result()[1].split("\n")[-1]
        if TYPE == "oss":
            assert any(name in res for name in ["bps_w","ops_w"]), "not found oss iostat output"
        else:
            assert any(name in res for name in ["open","close","stat","lstat","lcreate"]), "not found mds iostat output"
        sleep(2)