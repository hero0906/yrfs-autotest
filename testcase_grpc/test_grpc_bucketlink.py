# coding=utf-8
"""
@Desciption : grpc bucketlink
@Time : 2022/05/28
@Author : chenqiankun
Change: 2022/05/30 caoyi
"""

import logging
import grpc
import pytest
import time
import re
import os
from common.util import sshClient
from config import consts
from google.protobuf.json_format import MessageToDict
from common.grpc import bucketlink_pb2
from common.grpc import bucketlink_pb2_grpc
from common.grpc import bucket_pb2
from common.grpc import bucket_pb2_grpc
from common.grpc import setentry_pb2
from common.grpc import setentry_pb2_grpc
from common.grpc import mkdir_pb2
from common.grpc import mkdir_pb2_grpc
from common.grpc import blockio_pb2
from common.grpc import blockio_pb2_grpc
from common.util import YamlHandler

logger = logging.getLogger(__name__)


class TestGrpcBucket():

    def setup_class(self):
        # init the test info
        self.serverip = consts.META1  # cluster_ip
        self.endpoint = consts.GRPC_ENDPOINT  # agent_grpc port
        self.sshserver = sshClient(self.serverip)
        self.testdir_pre = "auotest_grpc_bucket"
        self.channel = ""
        try:
            logger.info("connect grpc server: %s" % self.endpoint)
            self.channel = grpc.insecure_channel(self.endpoint)
        except Exception as e:
            logger.error(e)
            pytest.skip(msg="grpc server connect failed.test skip")

        self.yaml_conf = YamlHandler("grpc_bucketlink")

    def teardown_class(self):
        self.sshserver.ssh_exec("cd %s&&rm -fr %s*" % (consts.MOUNT_DIR, self.testdir_pre))
        self.channel.close()
        self.sshserver.close_connect()

    def setup(self):
        time.sleep(10)

    @pytest.mark.parametrize("schema",(0,1,2))
    @pytest.mark.parametrize("use_mounted_path",(True, False))
    @pytest.mark.parametrize("pool_id",("", "12344"))
    @pytest.mark.parametrize("testpath",(True, False))
    def test_createdir(self, schema, use_mounted_path, pool_id,testpath):
        """
        测试mkdir和setentry接口
        """
        testdir = self.testdir_pre + str(time.time())
        force_set = False
        try:
            if testpath:
                # stub = mkdir_pb2_grpc.MkDirStub(self.channel)
                # rsp = stub.MkDir(mkdir_pb2.MkDirRequest(use_absolute_path=False,
                #                                         path=testdir))
                # logger.info(rsp)
                # assert rsp.result.error_code == 0, rsp.result.result
                self.sshserver.ssh_exec("cd %s&&mkdir -p %s" % (consts.MOUNT_DIR, testdir))
            if use_mounted_path:
                testdir = os.path.join(consts.MOUNT_DIR, testdir)
            if schema == 2:
                force_set = True
            if not testpath:
                testdir = "autotest-jfjgjjgr-23344"
            #set entry
            stub = setentry_pb2_grpc.SetEntryStub(self.channel)
            rsp = stub.SetEntry(setentry_pb2.SetEntryRequest(use_mounted_path=use_mounted_path,
                                                             path=testdir,pool_id=pool_id,
                                                             stripe_size="1M", stripe_count=4,
                                                             schema=schema,force_set=force_set))
            logger.info(rsp)
            if not testpath or pool_id:
                logger.info("wrong parameter expect result create dir failed.")
                assert rsp.result.error_code != 0, "test create dir success."
            else:
                logger.info("expect result create dir success.")
                assert rsp.result.error_code == 0, "test create dir failed."
        finally:
            if testpath:
                if use_mounted_path:
                    self.sshserver.ssh_exec("rm -fr %s" % (testdir))
                else:
                    self.sshserver.ssh_exec("cd %s&&rm -fr %s" % (consts.MOUNT_DIR, testdir))
            time.sleep(1)

    @pytest.mark.parametrize("s3", ("baidu", "ali", "ceph"))
    def test_testbucket(self, s3):
        """
        分别测试"baidu/ali/ceph"bucket连通性
        """
        if s3 == "ceph":
            grpc_host_name = consts.ceph_s3["hostname"]  # url:port
            grpc_bucket_name = consts.ceph_s3["bucketname"]
            grpc_access_key = consts.ceph_s3["access_key"]
            grpc_secret_access_key = consts.ceph_s3["secret_access_key"]
            uri_style = 0
        if s3 == "ali":
            grpc_host_name = consts.ali_s3["hostname"]  # url:port
            grpc_bucket_name = consts.ali_s3["bucketname"]
            grpc_access_key = consts.ali_s3["access_key"]
            grpc_secret_access_key = consts.ali_s3["secret_access_key"]
            uri_style = 1
        if s3 == "baidu":
            grpc_host_name = consts.baidu_s3["hostname"]  # url:port
            grpc_bucket_name = consts.baidu_s3["bucketname"]
            grpc_access_key = consts.baidu_s3["access_key"]
            grpc_secret_access_key = consts.baidu_s3["secret_access_key"]
            uri_style = 1

        stub = bucket_pb2_grpc.BucketStub(self.channel)
        bucket_config = bucket_pb2.BucketConfig(host_name=grpc_host_name,
                                                bucket_name=grpc_bucket_name, protocol=1, uri_style=uri_style,
                                                access_key=grpc_access_key, secret_access_key=grpc_secret_access_key,
                                                region="", lib_type=1)
        logger.info(bucket_config)
        rsp = stub.AddOrTestBucket(bucket_pb2.AddOrTestBucketRequest(
            op=1,
            bucket_config=bucket_config,
        ))
        logger.info(rsp)
        assert rsp.result.error_code == 0, "test bucket failed."

    @pytest.mark.parametrize("options",("grpc_host_name","grpc_bucket_name","grpc_access_key",
                            "grpc_secret_access_key","uri_style","lib_type","protocol"))
    @pytest.mark.parametrize("wrongpara", ("errorparameter", "", 123456))
    def test_testbucket_wrong(self, wrongpara, options):
        """
        测试bucket连通性错误参数，预期失败。
        """
        param_dict = {}
        param_dict["grpc_host_name"] = consts.ceph_s3["hostname"]  # url:port
        param_dict["grpc_bucket_name"] = consts.ceph_s3["bucketname"]
        param_dict["grpc_access_key"] = consts.ceph_s3["access_key"]
        param_dict["grpc_secret_access_key"] = consts.ceph_s3["secret_access_key"]
        param_dict["uri_style"] = 0
        param_dict["lib_type"] = 1
        param_dict["protocol"] = 1

        param_dict[options] = wrongpara

        stub = bucket_pb2_grpc.BucketStub(self.channel)
        try:
            bucket_config = bucket_pb2.BucketConfig(host_name=param_dict["grpc_host_name"],
                                                    bucket_name=param_dict["grpc_bucket_name"], protocol=param_dict["protocol"],
                                                    uri_style=param_dict["uri_style"], access_key=param_dict["grpc_access_key"],
                                                    secret_access_key=param_dict["grpc_secret_access_key"],
                                                    region="", lib_type=param_dict["lib_type"])
        except Exception:
            logger.info("wrong parameter")
            assert True
        else:
            rsp = stub.AddOrTestBucket(bucket_pb2.AddOrTestBucketRequest(
                op=1,
                bucket_config=bucket_config,
            ))
            logger.info(rsp)
            assert rsp.result.error_code != 0, "test bucket success."

    @pytest.mark.parametrize("s3", ("baidu", "ali", "ceph"))
    #@pytest.mark.parametrize("s3", ("ceph",))
    def test_createbucket(self, s3):
        """
        测试分别添加bucket"baidu/ali/ceph"
        """
        #添加bucket
        if s3 == "ceph":
            grpc_host_name = consts.ceph_s3["hostname"]  # url:port
            grpc_bucket_name = consts.ceph_s3["bucketname"]
            grpc_access_key = consts.ceph_s3["access_key"]
            grpc_secret_access_key = consts.ceph_s3["secret_access_key"]
            uri_style = 0
        if s3 == "ali":
            grpc_host_name = consts.ali_s3["hostname"]  # url:port
            grpc_bucket_name = consts.ali_s3["bucketname"]
            grpc_access_key = consts.ali_s3["access_key"]
            grpc_secret_access_key = consts.ali_s3["secret_access_key"]
            uri_style = 1
        if s3 == "baidu":
            grpc_host_name = consts.baidu_s3["hostname"]  # url:port
            grpc_bucket_name = consts.baidu_s3["bucketname"]
            grpc_access_key = consts.baidu_s3["access_key"]
            grpc_secret_access_key = consts.baidu_s3["secret_access_key"]
            uri_style = 1

        stub = bucket_pb2_grpc.BucketStub(self.channel)
        bucket_config = bucket_pb2.BucketConfig(host_name=grpc_host_name,
                                                bucket_name=grpc_bucket_name, protocol=1, uri_style=uri_style,
                                                access_key=grpc_access_key, secret_access_key=grpc_secret_access_key,
                                                region="", lib_type=1)
        logger.info(bucket_config)
        rsp = stub.AddOrTestBucket(bucket_pb2.AddOrTestBucketRequest(
            op=0,
            bucket_config=bucket_config,
        ))
        logger.info(rsp)
        assert rsp.result.error_code == 0, "add bucket failed."
        bucket_id_tmp = re.findall(".*id=(.*)", rsp.result.result)
        bucket_id = int("".join(bucket_id_tmp))
        #写入yaml
        data = {}
        if s3 == "baidu":
            data["baidu_bucketid"] = bucket_id
        if s3 == "ali":
            data["ali_bucketid"] = bucket_id
        if s3 == "ceph":
            data["ceph_bucketid"] = bucket_id
        self.yaml_conf.write_yaml(data)

    def test_listbucket(self):
        #列出已创建的bucket并确认是否存在
        stub = bucket_pb2_grpc.BucketStub(self.channel)
        rsp = stub.ListBuckets(bucket_pb2.ListBucketsRequest())
        for i in rsp:
            assert i.result.error_code == 0, "list bucket failed."
        mess = MessageToDict(i)
        bucket_ids = []
        for i in mess["bucketInfo"]:
            bucket_ids.append(i["bucketId"])
        data = self.yaml_conf.read_yaml()
        assert data["ceph_bucketid"] in bucket_ids, "not found bucketid"
        assert data["ali_bucketid"] in bucket_ids, "not found bucketid"
        assert data["baidu_bucketid"] in bucket_ids, "not found bucketid"

    @pytest.mark.parametrize("param", (1234678, "errorkey", "correctkey"))
    def test_updatebucket(self, param):
        """
        测试更新bucket配置
        """
        #获取ceph bucketid
        data = self.yaml_conf.read_yaml()
        bucket_id = data["ceph_bucketid"]
        grpc_access_key = consts.ceph_s3["access_key"]
        grpc_secret_access_key = consts.ceph_s3["secret_access_key"]

        if param == 1234678:
            bucket_id = param
        if param == "errorkey":
            grpc_access_key = param
            grpc_secret_access_key = param

        update_bucket_req = bucket_pb2.UpdateBucketRequest(
            bucket_id=bucket_id,
            access_key=grpc_access_key,
            secret_access_key=grpc_secret_access_key)
        logger.info(update_bucket_req)
        stub = bucket_pb2_grpc.BucketStub(self.channel)
        rsp = stub.UpdateBucket(update_bucket_req)
        logger.info(rsp)
        if param == "correctkey":
            logger.info("correct key, expected success.")
            assert rsp.result.error_code == 0,"update bucket failed."
        else:
            logger.info("error key, expected failed.")
            assert rsp.result.error_code != 0, "update bucket success."

    @pytest.mark.parametrize("testdir", ("fggjjjg",""))
    @pytest.mark.parametrize("bucketid", (12345697, None))
    def test_create_bucketlink_wrong(self, testdir, bucketid):
        """
        错误参数创建bucketlink,预期失败
        """
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        rsp = stub.AddBucketLink(bucketlink_pb2.AddBucketLinkRequest(
                link_root_dir=testdir, bucket_id=bucketid))
        logger.info(rsp)
        assert rsp.result.error_code != 0, "wrong param create bucketlink success"

    @pytest.mark.parametrize("s3",("ali","ceph","baidu","ceph2","ceph3"))
    def test_create_bucketlink(self, s3):
        """
=       正确参数创建bucketlink分别对接baidu、ali、ceph预期成功
        """
        testdir = self.testdir_pre + str(time.time())
        self.sshserver.ssh_exec("cd %s&&mkdir %s" % (consts.MOUNT_DIR, testdir))
        bucket_ids = self.yaml_conf.read_yaml()
        if s3 == "ceph2" or s3 ==  "ceph3":
            bucket_id = bucket_ids["ceph_bucketid"]
        else:
            bucket_id = bucket_ids[s3 + "_bucketid"]


        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        rsp = stub.AddBucketLink(bucketlink_pb2.AddBucketLinkRequest(
                link_root_dir=testdir, bucket_id=bucket_id))
        logger.info(rsp)
        assert rsp.result.error_code == 0, "create bucketlink failed."
        #获取bucketlink id
        link_id_tmp = re.findall(".*id=(.*)", rsp.result.result)
        link_id = int("".join(link_id_tmp))
        if link_id:
            logger.info("s3: %s %s make linkid: %s" % (s3, bucket_id ,link_id))
        else:
            logger.error("create bucketlink failed")
        #写入yaml
        data = {s3 + "_linkid": link_id}
        self.yaml_conf.write_yaml(data)

    @pytest.mark.parametrize("param",(0, 1))
    def test_stat_bucketlink(self, param):
        """
        stat bucketlink 正确id和错误id
        """
        link_id = 34443555
        data = self.yaml_conf.read_yaml()
        if param == 0:
            link_id = data["ceph_linkid"]
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        rsp = stub.StatBucketLink(bucketlink_pb2.StatBucketLinkRequest(
            link_id=link_id))
        for n in rsp:
            logger.info(n)
            if param == 0:
                assert n.result.error_code == 0,"stat buketlink failed."
            else:
                assert n.result.error_code != 0,"wrong id stat success."

    def test_export_blockio_notready(self):
        """
        非ready状态设置export blockio失败
        """
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.AddBlockLink(blockio_pb2.AddBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=1)))
        logger.info(rsp)
        assert rsp.result.error_code != 0, "not ready set export blockio success, expect fail."

    @pytest.mark.parametrize("param",(0, 1))
    def test_import_blockio(self, param):
        """
        测试import blockio bucketlink new状态下的blockio测试
        """
        link_id = 23334443
        if param == 0:
            data = self.yaml_conf.read_yaml()
            link_id = data["ceph_linkid"]
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.AddBlockLink(blockio_pb2.AddBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=0)))
        logger.info(rsp)
        if param == 0:
            assert rsp.result.error_code == 0, "add blockio failed."
        else:
            assert rsp.result.error_code != 0, "wrong linkid add blockio success."

    def test_list_import_blockio(self):
        """
        列出import blockio
        """
        time.sleep(5)
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.ListBlockLinks(blockio_pb2.ListBlockLinksRequest())
        for n in rsp:
            logger.info(n)
            assert n.result.error_code == 0, rsp.result.result
        res = MessageToDict(n)
        logger.info(n)
        link_ids = []
        for n in res["blockInfo"]:
            link_ids.append(n["linkId"])
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        assert link_id in link_ids, "not found link_id in blockio list"

    @pytest.mark.parametrize("scope, pattern, prefix",
        [(0,"",""),(1,"testfile",""),(2,"","test"),(3,"","")])
    def test_import(self, scope, pattern, prefix):
        """
        测试import bucketlink
        """
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        scope = scope
        pattern =pattern
        prefix = prefix
        load_type = 0

        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        import_config_req = bucketlink_pb2.ImportConfig(
            scope=scope,
            pattern=pattern,
            prefix=prefix,
            load_type=load_type)
        import_bucketlink_req = bucketlink_pb2.ImportBucketLinkRequest(
            link_id=link_id,
            import_config=import_config_req)
        rsp = stub.ImportBucketLink(import_bucketlink_req)
        logger.info(rsp)
        assert rsp.result.error_code == 0, "import failed."
        #检查import是否完成
        logger.info("check import stat")
        for i in range(60):
            stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
            rsp = stub.StatBucketLink(bucketlink_pb2.StatBucketLinkRequest(link_id=link_id))
            rsp = list(rsp)[0]
            res = MessageToDict(rsp)
            logger.info(res)
            link_state = res["state"]
            if link_state == "Ready":
                break
            time.sleep(5)
        else:
            assert False, "timeout, bucketlink import not finish."

    def test_import_not_new(self):
        """
        非new状态的bucketlink import
        """
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        scope = 0
        pattern = ""
        prefix = ""
        load_type = 0
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        import_config_req = bucketlink_pb2.ImportConfig(
            scope=scope,
            pattern=pattern,
            prefix=prefix,
            load_type=load_type)
        import_bucketlink_req = bucketlink_pb2.ImportBucketLinkRequest(
            link_id=link_id,
            import_config=import_config_req)
        rsp = stub.ImportBucketLink(import_bucketlink_req)
        logger.info(rsp)
        assert rsp.result.error_code == 0, "not new state bucketlink import success,expect failed."

    @pytest.mark.parametrize("param", (0, 1))
    def test_del_import_blockio(self, param):
        """
        删除import blockio测试,正确参数和错误参数0表示正确，1表示错误
        """
        link_id = 4344343
        if param == 0:
            data = self.yaml_conf.read_yaml()
            link_id = data["ceph_linkid"]
        logger.info("delete import blockio linkid: %s" % link_id)
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.DelBlockLink(blockio_pb2.DelBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=0)))
        logger.info(rsp)
        if param == 0:
            logger.info("expect result, delete link import blockio succes.")
            assert rsp.result.error_code == 0, "delete blockio"
        else:
            logger.info("expect result, wrong param linkid delete export blockio failed.")
            assert rsp.result.error_code != 0, "wrong param delete blockio failed."

    def test_blockio_not_new(self):
        """
        非new状态下bucketlink的blockio失败
        """
        time.sleep(2)
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.AddBlockLink(blockio_pb2.AddBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=0)))
        logger.info(rsp)
        assert rsp.result.error_code != 0,"not new state blockio success, expect fail."

    @pytest.mark.parametrize("param",(0,1))
    def test_export_blockio(self, param):
        """
        ready 状态下的export blockio操作,正确id和错误id
        """
        time.sleep(2)
        link_id = 99848433
        if param == 0:
            data = self.yaml_conf.read_yaml()
            link_id = data["ceph_linkid"]
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.AddBlockLink(blockio_pb2.AddBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=1)))
        logger.info(rsp)
        if param == 0:
            assert rsp.result.error_code == 0,"export blockio failed."
        else:
            assert rsp.result.error_code !=0,"wrong param export blockio success,expect fail."

    def test_del_no_export_bucketlink(self):
        """
        删除没有export bucketlink失败
        """
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        logger.info("detele not export bucketlink.")
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        del_bucketlink_req = bucketlink_pb2.DelBucketLinkRequest(
            link_id=link_id)
        rsp = stub.DelBucketLink(del_bucketlink_req)
        logger.info(rsp)
        logger.info("expect result, not export bucketlink delete failed.")
        assert rsp.result.error_code !=0,"delet bucketlink success."
        #验证未删除成功
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        rsp = stub.StatBucketLink(bucketlink_pb2.StatBucketLinkRequest(
            link_id=link_id))
        for n in rsp:
            logger.info(n)
            assert n.result.error_code == 0, "stat buketlink failed."

    @pytest.mark.parametrize("bucket,scope,pattern,prefix,name_rule,name_suffix,will_purge,purge_timing",
        [("old", 0, "", "", 0, "", 0, 0),
         ("old", 1, "", "", 0, "", 0, 1),
         ("old", 2, "", "", 0, "", 0, 0),
         ("old", 3, "testfile", "", 0, "", 0, 0),
         ("old", 4, "", "", 0, "test", 0, 0),
         ("new", 0, "", "", 0, "", 0, 0),
         ("new", 1, "", "", 0, "", 0, 1),
         ("new", 2, "", "", 0, "", 0, 0),
         ("new", 3, "testfile", "", 0, "", 0, 0),
         ("new", 4, "", "", 0, "test", 0, 0),
         ])
    def test_export(self, bucket,scope,pattern,prefix,name_rule,name_suffix,will_purge,purge_timing):
        """
        bucketlink export 操作,不同参数组合测试，预期成功
        """
        data = self.yaml_conf.read_yaml()
        link_id = data["ceph_linkid"]
        if purge_timing == 1:
            if bucket == "old":
                link_id = data["ceph2_linkid"]
            else:
                link_id = data["ceph3_linkid"]

        if bucket == "old":
            bucket_id = data["ceph_bucketid"]
        else:
            bucket_id = data["ali_bucketid"]

        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        export_config_req = bucketlink_pb2.ExportConfig(
            bucket_id=bucket_id,
            scope=scope,
            pattern=pattern,
            prefix=prefix,
            name_rule=name_rule,
            name_suffix=name_suffix,
            will_purge=will_purge,
            purge_timing=purge_timing)
        export_bucketlink_req = bucketlink_pb2.ExportBucketLinkRequest(
            link_id=link_id,
            export_config=export_config_req)
        rsp = stub.ExportBucketLink(export_bucketlink_req)
        logger.info(rsp)
        assert rsp.result.error_code == 0,"export failed."
        # #检查export是否完成
        # for i in range(60):
        #     stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        #     rsp = stub.StatBucketLink(bucketlink_pb2.StatBucketLinkRequest(link_id=link_id))
        #     rsp = list(rsp)[0]
        #     res = MessageToDict(rsp)
        #     logger.info(res)
        #     link_state = res["state"]
        #     if link_state == "Exported":
        #         break
        #     time.sleep(5)
        # else:
        #     assert False, "timeout, bucketlink export not finish."

    @pytest.mark.parametrize("linkid,scope,pattern,prefix,name_rule,name_suffix,will_purge,purge_timing",
        [(None, 0, "", "", 0, "", 0, 0),
         (12344442, 0, "", "", 0, "", 0, 0),
         (1, 9, "32", "ff", 9, "fsdf", 9, 9)
         ])
    def test_export_wrong(self, linkid,scope,pattern,prefix,name_rule,name_suffix,will_purge,purge_timing):
        """
        export参数错误导入失败
        """
        link_id = linkid
        data = self.yaml_conf.read_yaml()
        if linkid == 1:
            link_id = data["ceph_linkid"]
        bucket_id = data["ceph_bucketid"]

        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        export_config_req = bucketlink_pb2.ExportConfig(
            bucket_id=bucket_id,
            scope=scope,
            pattern=pattern,
            prefix=prefix,
            name_rule=name_rule,
            name_suffix=name_suffix,
            will_purge=will_purge,
            purge_timing=purge_timing)
        export_bucketlink_req = bucketlink_pb2.ExportBucketLinkRequest(
            link_id=link_id,
            export_config=export_config_req)
        rsp = stub.ExportBucketLink(export_bucketlink_req)
        logger.info(rsp)
        assert rsp.result.error_code != 0, "wrong param export success."

    @pytest.mark.parametrize("param",(0,1))
    def test_del_export_blockio(self, param):
        """
        删除export blockio,正确的id和错误的id
        """
        link_id = 33232233
        if param == 0:
            data = self.yaml_conf.read_yaml()
            link_id = data["ceph_linkid"]
        logger.info("delete export blockio linkid: %s" % link_id)
        stub = blockio_pb2_grpc.BlockIOStub(self.channel)
        rsp = stub.DelBlockLink(blockio_pb2.DelBlockLinkRequest(
            block_link_info=blockio_pb2.BlockLinkInfo(
                link_id=link_id, block_type=1)))
        logger.info(rsp)
        if param == 0:
            logger.info("expect result, delete link export blockio succes.")
            assert rsp.result.error_code == 0, "delete blockio failed,"
        else:
            logger.info("expect result, wrong param linkid delete export blockio failed.")
            assert rsp.result.error_code !=0 ,"wrong linkid delete succes."

    @pytest.mark.parametrize("param", (0,1))
    def test_del_bucketlink(self,param):
        """
        分别测试删除正确的bucketlink id和错误的id
        """
        link_id = 3434443
        if param == 0:
            data = self.yaml_conf.read_yaml()
            link_id = data["ceph_linkid"]
        logger.info("detele export bucketlink linkid: %s." % link_id)
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        del_bucketlink_req = bucketlink_pb2.DelBucketLinkRequest(
            link_id=link_id)
        rsp = stub.DelBucketLink(del_bucketlink_req)
        logger.info(rsp)
        if param == 0:
            logger.info("expect result, delete bucketlink success.")
            assert rsp.result.error_code == 0,"delete bucketlink failed."
        else:
            logger.info("expect result, wrong linkid delete bucketlink failed.")
            assert rsp.result.error_code != 0,"delete bucketlink failed."
        #验证删除成功
        time.sleep(5)
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        rsp = stub.StatBucketLink(bucketlink_pb2.StatBucketLinkRequest(
            link_id=link_id))
        for n in rsp:
            logger.info(n)
            assert n.result.error_code != 0, "stat buketlink failed."

    @pytest.mark.parametrize("s3",("ceph","ali","baidu"))
    @pytest.mark.parametrize("prefix,sub_op",[("",0),("test",0),("",1)])
    def test_subscribe(self, s3, prefix, sub_op):
        """
        ali、ceph、baidu订阅和取消订阅功能验证
        """
        data = self.yaml_conf.read_yaml()
        if s3 == "ali":
            s3_type = 1
            link_id = data["ali_linkid"]
        elif s3 == "baidu":
            s3_type = 2
            link_id = data["baidu_linkid"]
        else:
            s3_type = 3
            link_id = data["ceph_linkid"]

        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        sub_config_req = bucketlink_pb2.SubscribeConfig(
            s3_type=s3_type,
            prefix=prefix)
        bucketlink_subops_req = bucketlink_pb2.BucketLinkSubscribeOpsRequest(
            link_id=link_id,
            sub_op=sub_op,
            sub_config=sub_config_req)
        rsp = stub.BucketLinkSubscribeOps(bucketlink_subops_req)
        logger.info(rsp)

        assert rsp.result.error_code == 0,"subscribe failed."

    @pytest.mark.parametrize("s3", ("ceph", "ali", "baidu"))
    def test_subscribe_unset(self, s3):
        """
        订阅类型为unset测试
        """
        data = self.yaml_conf.read_yaml()
        link_id = data[s3 + "_linkid"]
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        sub_config_req = bucketlink_pb2.SubscribeConfig(
            s3_type=0,
            prefix="")
        bucketlink_subops_req = bucketlink_pb2.BucketLinkSubscribeOpsRequest(
            link_id=link_id,
            sub_op=0,
            sub_config=sub_config_req)
        rsp = stub.BucketLinkSubscribeOps(bucketlink_subops_req)
        logger.info(rsp)
        logger.info("expect result, unset type subcribe failed.")
        assert rsp.result.error_code != 0, "subcribe success."

    @pytest.mark.parametrize("s3", ("ceph", "ali", "baidu"))
    def test_del_bucketlink(self, s3):
        """
        测试删除bucketlink
        """
        data = self.yaml_conf.read_yaml()
        link_id = data[s3 + "_linkid"]
        stub = bucketlink_pb2_grpc.BucketLinkStub(self.channel)
        del_bucketlink_req = bucketlink_pb2.DelBucketLinkRequest(
            link_id=link_id)
        rsp = stub.DelBucketLink(del_bucketlink_req)
        logger.info(rsp)
        assert rsp.result.error_code == 0, "delete bucketlink failed."