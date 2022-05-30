#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Desciption : qos grpc test
@Time : 2022/05/16
@Author : chenqiankun
"""

import acl_pb2
import acl_pb2_grpc
import grpc

def run():
    # connect to the rpc server
    channel = grpc.insecure_channel("localhost:8000")
    # call the rpc service
    stub = acl_pb2_grpc.AclStub(channel)
    response = stub.ListAcl(acl_pb2_grpc.ListAclPara(path=''))
    code = response.result.error_code
    print("Response error_code" + code)


if __name__ == '__main__':
    run()

