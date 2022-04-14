import logging

from common import grpc

from krypton.host.grpc import agent_pb2
from krypton.host.grpc import agent_pb2_grpc


def mds_test():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = agent_pb2_grpc.AgentStub(channel)
        response = stub.MdsOverview(agent_pb2.MdsOverviewPara())
        print 'disk_space_total: %s' % response.disk_space_total
        print 'disk_space_free: %s' % response.disk_space_free
        print 'disk_space_used: %s' % response.disk_space_used
        print 'inode_space_used: %s' % response.inode_space_used
        # import pdb;pdb.set_trace()
        for i in response.node_info:
            print i.node_name
            print i.node_num_id
            print i.online
    # for i in response.work_requests:
    #    print i
    # for i in response.queued_requests:
    #    print i


def oss_test():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = agent_pb2_grpc.AgentStub(channel)
        response = stub.OssOverview(agent_pb2.OssOverviewPara())
        print 'disk_space_total: %s' % response.disk_space_total
        print 'disk_space_free: %s' % response.disk_space_free
        print 'disk_space_used: %s' % response.disk_space_used
        print 'disk_read_sum: %s' % response.disk_read_sum
        print 'disk_write_sum: %s' % response.disk_write_sum
        for i in response.node_info:
            print i.node_name
            print i.node_num_id
            print i.online


def nodes_test():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = agent_pb2_grpc.AgentStub(channel)
        rsp = stub.NodeList(agent_pb2.NodeListPara(client=True,
                                                   hide_internal_ips=False,
                                                   agent=True))
        for i in rsp:
            for x in i.node_lists:
                print '-----------------------------------'
                print 'node type: %s' % x.type
                print 'node number id: %s' % x.node_num_id
                print 'node name: %s' % x.node_name


def client_test(node_type=1):
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = agent_pb2_grpc.AgentStub(channel)
        rsp = stub.ClientStats(agent_pb2.ClientStatsPara(node_type=node_type,
                                                         hide_internal_ips=False,
                                                         return_zero_stats=True))
        for i in rsp:
            print '-----------------------------------'
            print i.ip
            print i.online
            print i.opcounters


def sla_test():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = agent_pb2_grpc.AgentStub(channel)
        rsp = stub.GetSlaInfo(agent_pb2.GetSlaInfoPara(with_root=True))
        for i in rsp:
            print '-----------------------------------'
            print i.path
            print i.entry_id
            print i.sla_value


if __name__ == '__main__':
    logging.basicConfig()
    print '========== mds test =========='
    mds_test()
    print '========== oss test =========='
    oss_test()
    print '========== nodes test ========='
    nodes_test()
    print '========== client mds test =========='
    client_test(node_type=1)
    print '========== client oss test =========='
    client_test(node_type=2)
    print '========== sla test =========='
    sla_test()
