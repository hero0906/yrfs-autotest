# coding=utf-8
import os

'''
@Description  : 用于存放全局变量
@Time    : 2019/12/05 14:52
@Author  : caoyi
'''
# 测试用例集 可选测试用例集 smokeTest、stablityTest、serviceTest、allTest、funcTest、collect
CASE_TYPE = "allTest"
#version 660 663 664 670
YRFS_VERSION = "670"

#CLIENT = ["192.168.96.253", "192.168.96.254"]
META1 = "10.16.2.11"
CLIENT = ["10.16.2.17", "10.16.2.18"]
# META1 = "192.168.0.23"
# CLIENT = ["192.168.0.40"]
# 集群ssh用户名密码
USERNAME = "root"
PASSWORD = "Passw0rd"

WINCLIENT = "10.16.2.16"
NFS_PORT = 7735

GRPC_ENDPOINT_PORT = 8000
GRPC_ENDPOINT = "%s:%s" % (META1, GRPC_ENDPOINT_PORT)

CLIENT_CONFIG = "/etc/yrfs/yrfs-client.conf"
CLIENT_MOUNT_FILE = "/etc/yrfs/yrfs-mounts.conf"
CLIENT_NET_FILE = '/etc/yrfs/net'


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTDATA_PATH = os.path.join(BASE_PATH, 'testdata')
LOG_PATH = os.path.join(BASE_PATH, 'logs')
# TEST_REPORT = os.path.join(BASE_PATH, 'report')

MOUNT_DIR = "/mnt/yrfs"

# s3配置信息
s3 = {
    # "hostname": "10.16.13.12:7480",
    "hostname": "192.168.0.26:7480",
    # "bucketname": "zh_ossbucket",
    "bucketname": "auto-cy1",
    "bucketmirror": "auto-cy2",
    # "access_key": "9X4U5WAL4NZHAY6PBTG6",
    "access_key": "UGRKZNLT1JE57ZCTRVBD",
    # "secret_access_key": "qmEZRml9vurEB9NPSxnpdDlKH5dWdI5NPG1wyIrq",
    "secret_access_key": "AP2jwL9aVYPYt5w7wXuXBwgb8GdV6bglVcq1qKVO",
    "region": "",
    "token": "",
    "type": "libs3",
    "protocol": "1",
    "uri_style": "1",
    "bucketid": "9006",
    "mirrorid": "9007"
}

# windows http server配置
REST_SERVER = "10.16.2.18:3000"
# vcenter 配置：
vcenter = {
    "host": "192.168.0.10",
    "user": "administrator@vsphere.local",
    "passwd": "Passw0rd@123",
    "port": "443",
    "disable_ssl_verification": "True"
}
