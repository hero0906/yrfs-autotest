# coding=utf-8
'''
@Desciption : grpc mds overview
@Time : 2021/06/19
@Author : yuanmingpeng
'''
import time
import grpc
import pytest
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from common.grpc import agent_pb2
from common.grpc import agent_pb2_grpc
from depend.client import client_mount

#@pytest.mark.skip(reason="no teardown")
@pytest.mark.funcTest
class TestGrpcSLA(YrfsCli):

    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.endpoint = consts.GRPC_ENDPOINT
        self.sshclient = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        #添加客户端的acl权限
        self.acl_id = "autotest-grpc"
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_add", "", self.acl_id,"rw"))

    def teardown_class(self):
        #清理测试数据
        testdir = 'grpc_sla_quota_dir2'
        self.sshclient.ssh_exec("rm -fr %s/%s/grpc_sla_file" % (consts.MOUNT_DIR, testdir))
        self.sshclient.ssh_exec("rm -rf %s/%s" % (consts.MOUNT_DIR, testdir))
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_del", "", self.acl_id))
        #关闭ssh会话
        self.sshserver.close_connect()
        self.sshclient.close_connect()

    def test_overview(self):
        '''
        测试grpc sla监控信息获取
        '''
        # 客户端业务执行
        mount_stat = client_mount(self.clientip,aclid=self.acl_id)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed test skip.")

        yrcli = YrfsCli()
        testdir = 'grpc_sla_quota_dir2'
        testpath1 = consts.MOUNT_DIR + "/" + testdir

        make_dir = self.get_cli('mkdir', testdir, 'nomirror')
        self.sshserver.ssh_exec(make_dir)

        cmd = yrcli.get_cli("quota_remove", testdir)
        self.sshserver.ssh_exec(cmd)

        cmd = yrcli.get_cli("quota_set", testdir, "20G", "1000")
        status, result = self.sshserver.ssh_exec(cmd)
        assert status == 0

        get_entry_cmd = yrcli.get_cli("get_file_entry", testpath1)
        status, result = self.sshserver.ssh_exec(get_entry_cmd)
        assert status == 0
        entry_id = None
        for l in result.split('\n'):
            if l.startswith('ID'):
                id_info = l.split(',')[0]
                entry_id = id_info.split(':')[-1].strip()

        fio_cmd = "nohup fio -iodepth=32 -numjobs=4 -bs=1M -size=50M -rw=rw -time_based -runtime=20 " \
                  "-filename=%s/%s/grpc_sla_file -ioengine=psync -group_reporting " \
                  "-name=test &" % (consts.MOUNT_DIR, testdir)
        self.sshclient.ssh_exec(fio_cmd)
        time.sleep(15)

        results = []
        with grpc.insecure_channel(self.endpoint) as channel:
            stub = agent_pb2_grpc.AgentStub(channel)
            rsp = stub.GetSlaInfo(agent_pb2.GetSlaInfoPara(with_root=True))
            for x in rsp:
                vals = x.sla_value
                rbps = vals[4]
                wbps = vals[5]
                riops = vals[6]
                wiops = vals[7]
                results.append((
                    x.entry_id,
                    x.path,
                    rbps,
                    wbps,
                    riops,
                    wiops,
                    rbps + wbps,
                    riops + wiops
                ))
        mount_root_points = False
        time.sleep(10)
        for sla in results:
            if str(sla[0]) == entry_id:
                # IOPS_KEY, sla[7]
                # READ_IOPS_KEY, sla[4]
                # WRITE_IOPS_KEY, sla[5]
                # BANDWIDTH_KEY, sla[6]
                # READ_BANDWIDTH_KEY, sla[2]
                # WRITE_BANDWIDTH_KEY, sla[3]
                mount_root_points = True
        self.sshclient.ssh_exec("killall -9 fio")
        #         assert sla[7] > 0
        #         assert sla[4] > 0
        #         assert sla[5] > 0
        #         assert sla[6] > 0
        #         assert sla[2] > 0
        #         assert sla[3] > 0
        # assert mount_root_points