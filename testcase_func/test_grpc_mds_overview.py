# coding=utf-8
'''
@Desciption : grpc mds overview
@Time : 2021/06/19
@Author : yuanmingpeng
'''
import time
import grpc
import pytest
import logging
from common.cli import YrfsCli
from common.util import sshClient
from config import consts
from common.grpc import agent_pb2
from common.grpc import agent_pb2_grpc

logger = logging.getLogger(__name__)

#@pytest.mark.skip(reason="skip")
@pytest.mark.funcTest
class TestGrpcMdsOverview(YrfsCli):

    def setup_class(self):
        self.serverip = consts.META1
        self.clientip = consts.CLIENT[0]
        self.endpoint = consts.GRPC_ENDPOINT
        self.sshclient1 = sshClient(self.clientip)
        self.sshserver = sshClient(self.serverip)
        #添加客户端的acl权限
        self.acl_id = "autotest-grpc"
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_add", "", self.acl_id,"rw"))

    def teardown_class(self):
        self.sshclient1.ssh_exec("rm -fr %s/grpc_mds_overview_file" % consts.MOUNT_DIR)
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_del", "", self.acl_id))
        #关闭ssh会话
        self.sshserver.close_connect()
        self.sshclient1.close_connect()

    def test_overview(self):
        '''
        测试mds监控信息获取
        '''
        # 客户端业务执行
        fio_cmd = "nohup fio -iodepth=32 -numjobs=4 -bs=1M -size=50M -rw=rw -time_based -runtime=20 " \
                  "-filename=%s/grpc_mds_overview_file -ioengine=psync -group_reporting " \
                  "-name=test &" % consts.MOUNT_DIR
        self.sshclient1.ssh_exec(fio_cmd)
        time.sleep(15)

        with grpc.insecure_channel(self.endpoint) as channel:
            stub = agent_pb2_grpc.AgentStub(channel)
            rsp = stub.MdsOverview(agent_pb2.MdsOverviewPara())
        logger.info("get cluster grpc info: %s" % rsp)
        self.sshclient1.ssh_exec("killall -9 fio")
        # assert rsp.disk_space_total > 0
        # assert rsp.disk_space_free > 0
        # assert rsp.disk_space_used > 0
        # assert rsp.inode_space_used > 0
        # # 待确认，读写情况接口返回是否大于0
        # assert len(rsp.queued_requests) > 0
        # assert len(rsp.work_requests) > 0
        # assert rsp.queued_requests[-1].value == 0
        # assert rsp.work_requests[-1].value > 0