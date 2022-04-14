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
from depend.client import client_mount

logger = logging.getLogger(__name__)

OSS_OPCOUNTER = [
    'sum',
    'ack',
    's_ch_drct',
    'get_file_size',
    's_attr',
    'statfs',
    'trunc',
    'close',
    'fsync',
    'open',
    'iops_rd',
    'bps_rd',
    'iops_wr',
    'bps_wr',
    'gendbg',
    'hrtbeat',
    'rem_node',
    'node_inf',
    'stor_info',
    'unlnk'
]

#@pytest.mark.skip(reason="not need run")
@pytest.mark.funcTest
class TestGrpcClientStat(YrfsCli):

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
        self.sshclient1.ssh_exec("rm -fr %s/grpc_client_stat_file" %consts.MOUNT_DIR)
        self.sshserver.ssh_exec(self.get_cli(self, "acl_id_del", "", self.acl_id))
        self.sshserver.close_connect()
        self.sshclient1.close_connect()

    def test_overview(self):
        '''
        测试client监控信息获取
        '''
        # 客户端挂载业务执行
        mount_stat = client_mount(self.clientip,aclid=self.acl_id)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed test skip.")

        fio_cmd = "nohup fio -iodepth=16 -numjobs=4 -bs=1M -size=20M -rw=rw -time_based -runtime=20 " \
                  " -filename=%s/grpc_client_stat_file -ioengine=psync -group_reporting " \
                  "-name=test &" % consts.MOUNT_DIR
        self.sshclient1.ssh_exec(fio_cmd)
        time.sleep(15)

        node_type = 'stor'
        with grpc.insecure_channel(self.endpoint) as channel:
            stub = agent_pb2_grpc.AgentStub(channel)
            rsp = stub.ClientStats(agent_pb2.ClientStatsPara(node_type=2,
                                                             hide_internal_ips=True,
                                                             return_zero_stats=True,
                                                             client_stats_type=1))
        #     cluster_dict, clients = {}, []
        #     for client in rsp:
        #         ip = client.ip
        #         counters = client.opcounters
        #         online = client.online
        #         if ip == 'total':
        #             for index, v in enumerate(counters):
        #                 k = node_type + "_" + OSS_OPCOUNTER[index]
        #                 cluster_dict[k] = v
        #         else:
        #             c = dict()
        #             c['ip'] = ip
        #             c['online'] = online
        #             if online:
        #                 for index, v in enumerate(counters):
        #                     c[node_type + "_" + OSS_OPCOUNTER[index]] = v
        #                 if c:
        #                     clients.append(c)
        # logger.info("grpc clients info: %s" % clients)
        # logger.info("grpc cluster info: %s" % cluster_dict)
        #
        # time.sleep(5)
        # assert cluster_dict != {}
        # assert cluster_dict['stor_iops_rd'] > 0
        # assert cluster_dict['stor_bps_rd'] > 0
        # assert cluster_dict['stor_iops_wr'] > 0
        # assert cluster_dict['stor_bps_wr'] > 0

        # for c in clients:
        #     logger.info("check client sla info: %s." % c)
        #     cmd = 'ip a|grep %s' % c['ip']
        #     status, result = self.sshclient1.ssh_exec(cmd)
        #     # c is matched with client1
        #     if status == 0:
        #         # assert c['stor_iops_rd'] > 0
        #         # assert c['stor_bps_rd'] > 0
        #         # assert c['stor_iops_wr'] > 0
        #         # assert c['stor_bps_wr'] > 0
        #         # assert c['online'] == True
        #         break
        self.sshclient1.ssh_exec("killall -9 fio")
        # assert status == 0, "cannot find client sla."