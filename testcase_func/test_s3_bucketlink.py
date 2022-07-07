# coding=utf-8
"""
@Desciption : s3 bucketlink case.
@Time : 2022/06/17 15:28
@Author : caoyi
"""
import os
import re
import time
import pytest
from common.s3cmd import S3Object
from common.util import sshClient, shell
from config import consts
from common.s3depend import get_bucketlink_stat

class TestbucketLink:
    def setup_class(self):
        self.serverip = consts.CLUSTER_VIP
        self.sshserver = sshClient(self.serverip)
        # 创建bucket
        add_bucket = "yrcli --bucket --op=add --hostname={0} --protocol=1 --bucketname={1} " \
                     "--uri_style=1 --access_key={2} --secret_access_key={3} --type=aws".format(
            consts.s3["hostname"], consts.s3["bucketname"], consts.s3["access_key"],
            consts.s3["secret_access_key"])
        stat, res = self.sshserver.ssh_exec(add_bucket)
        assert stat == 0, "add bucket failed."
        self.bucket_id = re.findall(r"Bucket-Id: (\d+)", res)[0]
        # 创建mirrorbucket
        add_bucket = "yrcli --bucket --op=add --hostname={0} --protocol=1 --bucketname={1} " \
                     "--uri_style=1 --access_key={2} --secret_access_key={3} --type=aws".format(
            consts.s3["hostname"], consts.s3["bucketmirror"], consts.s3["access_key"],
            consts.s3["secret_access_key"])
        stat, res = self.sshserver.ssh_exec(add_bucket)
        assert stat == 0, "add bucket failed."
        self.mirror_bucket_id = re.findall(r"Bucket-Id: (\d+)", res)[0]
        # 创建测试文件test1 test2 cy1
        self.test_datapath = "/autotest_bucketlink" + str(time.time())
        shell("mkdir -p " + self.test_datapath)
        self.testfile1 = "autotest001"
        self.testfile2 = "autotest002"
        self.testfile3 = "cytest001"
        shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (self.test_datapath, self.testfile1))
        shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (self.test_datapath, self.testfile2))
        shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (self.test_datapath, self.testfile3))
        # 上传文件至bucket中
        new_s3obj = S3Object()
        new_s3obj.bucket_clean()
        new_s3obj.upload(os.path.join(self.test_datapath, self.testfile1))
        new_s3obj.upload(os.path.join(self.test_datapath, self.testfile2))
        new_s3obj.upload(os.path.join(self.test_datapath, self.testfile3))
        # 清理临时测试文件
        os.system("rm -fr " + self.test_datapath)

    def setup(self):
        self.testdir = "autotest_bucketlink" + str(time.time())
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        # 创建测试目录
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)

    def teardown(self):
        # 删除测试目录
        self.sshserver.ssh_exec("rm -fr " + self.testpath)

    def teardown_class(self):
        self.sshserver.close_connect()

    @pytest.mark.parametrize("scope", (1, 2, 3, 4))
    @pytest.mark.parametrize("preload", (1, 2))
    @pytest.mark.parametrize("import_type", ("import", "block_import"))
    def test_import(self, scope, preload, import_type):
        """
        bucketlink导入文件测试，1:import all,2:import name matched,3:import prefix matched,4:import none
        meta only or meta and data
        """
        # 创建bucetlink
        add_link = "yrcli --bucketlink --op=add --path={0} --preload={3} --import_scope={2}" \
                   " --bucketid={1} -u".format(self.testdir,
                                                        self.bucket_id, scope, preload)
        if scope == 2:
            add_link = add_link + " --import_pattern=" + self.testfile1
        if scope == 3:
            add_link = add_link + " --import_prefix=cytest"
        stat, res = self.sshserver.ssh_exec(add_link)
        assert stat == 0, "add bucketlink failed"
        # 获取bucketlink id
        time.sleep(1)
        link_id = res.split("=")[1]
        _, res = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|tail -n 1")
        assert link_id == res, "bucketlink not found"
        # 导入文件
        stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=%s --linkid=%s" % (import_type, link_id))
        assert stat == 0,"import cmd failed."
        time.sleep(2)
        if import_type != "block_import" and scope != 4:
            for i in range(30):
                state = get_bucketlink_stat(link_id)
                if state["State"] == "Ready":
                    break
                else:
                    time.sleep(2)
            else:
                assert False, "import timeout."
        #查看文件是否导入成功
        _, res = self.sshserver.ssh_exec("ls " + self.testpath)
        rsp = get_bucketlink_stat(link_id)
        if scope == 1:
            files = res.split("\n")
            assert self.testfile1 in files
            assert self.testfile2 in files
            assert self.testfile3 in files, "import all fail"
            assert rsp["ImMetaFinished"] == "3", "import meta number does not match"
            if preload == 2:
                assert rsp["ImDataFinished"] == "3", "import data number does not match"
        if scope == 2:
            assert self.testfile1 == res, "import name matched fail"
            assert rsp["ImMetaFinished"] == "1", "import meta number does not match"
            if preload == 2:
                assert rsp["ImDataFinished"] == "1", "import data number does not match"
        if scope == 3:
            assert self.testfile3 == res, "import prefix matched"
            assert rsp["ImMetaFinished"] == "1", "import meta number does not match"
            if preload == 2:
                assert rsp["ImDataFinished"] == "1", "import data number does not match"
        if scope == 4:
            assert res == None, "import none fail"
        #执行导出删除目录
        stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=export --linkid=" + link_id)
        assert stat == 0, "export bucket failed"
        # stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=stat --linkid=" + link_id)
        # assert stat != 0, "delete bucketlink dir failed."
        #if import_type != "block_import" and scope != 4:
        time.sleep(2)
        for i in range(60):
            state = get_bucketlink_stat(link_id)
            if state["State"] == "Exported":
                break
            else:
                time.sleep(2)
        else:
            assert False, "export failed."
        # 删除bucketlink
        stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=del --linkid=" + link_id)
        assert stat == 0, "delete buckelink failed."
        stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|grep " + link_id)
        assert stat != 0, "delete bucketlink failed."
        stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=stat --linkid=" + link_id)
        assert stat != 0, "bucketlink delete failed."

    @pytest.mark.parametrize("scope", (1,2,3,4,5,6,7))
    @pytest.mark.parametrize("rule",(1,2))
    @pytest.mark.parametrize("purge",(0,1,2))
    @pytest.mark.parametrize("bucket",("old","new"))
    @pytest.mark.parametrize("export_type",("export","block_export"))
    def test_export(self, scope, rule, purge, bucket, export_type):
        """
        验证不同参数下的export预期结果正确。
        """
        # 创建新的bucket
        link_id = ""
        bucket_id = self.bucket_id
        bucket_name = consts.s3["bucketname"]
        # 清除bucket
        if bucket == "new":
            bucket_id = self.mirror_bucket_id
            bucket_name = consts.s3["bucketmirror"]
            new_s3obj = S3Object(bucket=bucket_name)
            new_s3obj.bucket_clean()
        try:
            #创建bucketlink
            add_link = "yrcli --bucketlink --op=add --path={0} -u --bucketid={1} --import_scope=1" \
                       " --export_bucketid={2} --export_scope={3} --name_rule={4}".format(
                        self.testdir,self.bucket_id,bucket_id,scope,rule)
            if purge != 0:
                add_link = add_link + " --will_purge=true --purge_timing=%s" % purge
            if scope == 4 or scope == 6:
                add_link = add_link + " --export_pattern=cytest001"
            if scope == 5 or scope == 7:
                add_link = add_link + " --export_prefix=cytest"
            if rule == 2:
                add_link = add_link + " --name_suffix=cy"
            stat, res = self.sshserver.ssh_exec(add_link)
            assert stat == 0, "add bucketlink failed."
            link_id = res.split("=")[1]
            #执行导入操作
            self.sshserver.ssh_exec("yrcli --bucketlink --op=import --linkid=" + link_id)
            time.sleep(2)
            #重写文件
            if scope == 3:
                self.sshserver.ssh_exec("dd if=/dev/zero of=%s/%s bs=512K count=1" % (self.testpath, self.testfile3))
            if scope == 6 or scope == 7:
                self.sshserver.ssh_exec("dd if=/dev/zero of=%s/%s bs=512K count=1" % (self.testpath, self.testfile3))
                self.sshserver.ssh_exec("dd if=/dev/zero of=%s/%s bs=512K count=1" % (self.testpath, self.testfile2))
            #执行导出操作
            stat, res = self.sshserver.ssh_exec("yrcli --bucketlink --op=%s --linkid=%s" % (export_type, link_id))
            assert stat == 0,"export oper failed."
            #验证导出动作
            time.sleep(2)
            for i in range(60):
                state = get_bucketlink_stat(link_id)
                if state:
                    if state["State"] == "Exported":
                        break
                    else:
                        time.sleep(2)
                else:
                    break
            else:
                assert False, "export timeout."
            #验证导出正确
            new_s3obj = S3Object(bucket=bucket_name)
            obj_keys = new_s3obj.get_keys(content=True)
            #判断不同scope文件导出情况
            name_suffix = ""
            if rule == 2:
                name_suffix = "cy"
            if bucket == "new":
                if scope != 1:
                    assert self.testfile3 + name_suffix in obj_keys, "export match failed."
                    if scope == 2:
                        assert self.testfile1 + name_suffix in obj_keys, "export match failed."
                        assert self.testfile2 + name_suffix in obj_keys, "export match failed."
                    else:
                        assert self.testfile1 + name_suffix not in obj_keys, "export match failed."
                        assert self.testfile2 + name_suffix not in obj_keys, "export match failed."
            else:
                assert self.testfile3 in obj_keys, "export match failed."
                assert self.testfile2 in obj_keys, "export match failed."
                assert self.testfile1 in obj_keys, "export match failed."
                if rule == 2:
                    if scope != 1:
                        if scope == 2:
                            assert self.testfile1 + name_suffix in obj_keys, "export match failed."
                            assert self.testfile2 + name_suffix in obj_keys, "export match failed."
                            assert self.testfile3 + name_suffix in obj_keys, "export match failed."
                        else:
                            assert self.testfile3 + name_suffix in obj_keys, "export match failed."
            #验证purge情况
            if purge == 1:
                #删除link后数据自动清空,暂时不支持
                self.sshserver.ssh_exec("yrcli --bucketlink --op=del --linkid=" + link_id)
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|grep " + link_id)
                assert stat != 0, "delete bucketlink failed."
                #stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=stat --linkid=" + link_id)
                # assert stat == 0,"empty bucketlink dir failed."
            elif purge == 2:
                #自动清空数据和目录,查询id不存在
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=stat --linkid=" + link_id)
                assert stat == 0,"empty bucketlink dir failed."
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|grep " + link_id)
                assert stat == 0, "bucketlink deleted."
                stat, _ = self.sshserver.ssh_exec("ls " + self.testpath)
                assert stat != 0, "empty bucketlink dir failed."
            else:
                #查询id正常存在
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|grep " + link_id)
                assert stat == 0, "bucketlink deleted."
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=list|awk '{print $1}'|grep " + link_id)
                assert stat == 0, "bucketlink deleted."
                stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=stat --linkid=" + link_id)
                assert stat == 0, "bucketlink directory is deleted."
        finally:
            self.sshserver.ssh_exec("yrcli --bucketlink --op=del --linkid=" + link_id)
            #清空bucket数据避免对下次的测试产生影响
            if bucket == "old":
                new_s3obj = S3Object(bucket=bucket_name)
                obj_keys = new_s3obj.get_keys(content=True)
                new_keys = [s for s in obj_keys if "cy" in s[-2:]]
                for key in new_keys:
                    new_s3obj.bucket_clean(key_name=key)

#@pytest.mark.skip
class Testsubscribe:
    def setup_class(self):
        self.serverip = consts.CLUSTER_VIP
        self.clientip = consts.CLIENT[0]
        self.sshserver = sshClient(self.serverip)
        # 创建bucket需要ceph s3
        s3_type = consts.ceph_s3
        add_bucket = "yrcli --bucket --op=add --hostname={0} --protocol=1 --bucketname={1} " \
                     "--uri_style=1 --access_key={2} --secret_access_key={3} --type=aws".format(
            s3_type["hostname"], s3_type["bucketname"], s3_type["access_key"],
            s3_type["secret_access_key"])
        stat, res = self.sshserver.ssh_exec(add_bucket)
        assert stat == 0, "add bucket failed."
        self.bucket_id = re.findall(r"Bucket-Id: (\d+)", res)[0]
        self.topic_prefix = "caoyi"
        #创建订阅topic
        self.new_s3object = S3Object(endpoint=s3_type["hostname"],access_key=s3_type["access_key"],
                                     secret_key=s3_type["secret_access_key"],bucket=s3_type["bucketname"])
        self.new_s3object.create_topic_notify(prefix=self.topic_prefix)
        #清空bucket
        self.new_s3object.bucket_clean()
    def setup(self):
        self.testdir = "autotest_bucketlink" + str(time.time())
        self.testpath = os.path.join(consts.MOUNT_DIR, self.testdir)
        # 创建测试目录
        self.sshserver.ssh_exec("mkdir -p " + self.testpath)

    def teardown(self):
        # 删除测试目录
        self.sshserver.ssh_exec("rm -fr " + self.testpath)

    def teardwon_class(self):
        self.sshserver.close_connect()

    def test_subscribe(self):
        """
        测试订阅功能正常,包括创建和删除操作。
        """
        prefix = self.topic_prefix
        testfile1 = prefix + "001"
        testfile2 = prefix + "002"
        testfile3 = "autotest001"
        data_dir = "/autotest_bucketlink" + str(time.time())
        link_id = ""
        try:
            shell("mkdir -p " + data_dir)
            # 创建bucetlink
            add_link = "yrcli --bucketlink --op=add --path={0} --bucketid={1} " \
                       "--import_prefix={2} --import_scope=3 -u".format(self.testdir, self.bucket_id, prefix)
            stat, res = self.sshserver.ssh_exec(add_link)
            link_id = res.split("=")[1]
            # 执行一次导入
            self.sshserver.ssh_exec("yrcli --bucketlink --op=import --linkid=" + link_id)
            time.sleep(5)
            #执行订阅操作
            stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=subscribe --linkid={0} --s3type=ceph "
                                    "--prefix={1}".format(link_id, prefix))
            assert stat == 0,"create subscribe failed."
            time.sleep(5)
            #上传数据验证订阅是否成功
            shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (data_dir,testfile1))
            shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (data_dir,testfile2))
            shell("dd if=/dev/zero of=%s/%s bs=1M count=1" % (data_dir, testfile3))
            self.new_s3object.upload(os.path.join(data_dir,testfile1))
            self.new_s3object.upload(os.path.join(data_dir,testfile2))
            self.new_s3object.upload(os.path.join(data_dir, testfile3))
            time.sleep(5)
            _, res = self.sshserver.ssh_exec("ls " + self.testpath)
            files = res.split("\n")
            assert testfile1 in files, "subscribe create failed."
            assert testfile2 in files, "subscribe create failed."
            state = get_bucketlink_stat(link_id)
            assert state["SubscribeCreated"] == "2", "link state wrong."
            #删除数据验证订阅删除
            self.new_s3object.bucket_clean(key_name=testfile1)
            time.sleep(5)
            state = get_bucketlink_stat(link_id)
            assert state["SubscribeDeleted"] == "1", "SubscribeDeleted num wrong."
            _, res = self.sshserver.ssh_exec("ls " + self.testpath)
            files = res.split("\n")
            assert testfile1 not in files, "subscribe delete file failed."
            assert testfile2 in files, "subscribe delete file failed."
        finally:
            #清理数据
            stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=export --linkid=" + link_id)
            assert stat == 0,"export failed"
            stat, _ = self.sshserver.ssh_exec("yrcli --bucketlink --op=del --linkid=" + link_id)
            assert stat == 0,"delete bucketlink failed."
            shell("rm -fr " + data_dir)