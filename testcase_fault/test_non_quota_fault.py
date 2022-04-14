# coding=utf-8
"""
@Desciption : Non-empty quota fault suite.
@Time : 2021/08/26 11:05
@Author : caoyi
"""
import pytest
import logging
from time import sleep
from config import consts
from common.util import sshClient, sshSftp
from depend.client import client_mount
from common.cli import YrfsCli
from common.fault import makeFault
from common.cluster import check_cluster_health

logger = logging.getLogger(__name__)


@pytest.mark.faultTest
class Test_nonquotaFalut(YrfsCli):

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1
        sshserver = sshClient(self.serverip)
        sshclient = sshClient(self.clientip)
        sshsftp = sshSftp(self.clientip)

        self.testdir = "autotest_quota_falut"
        self.testpath = consts.MOUNT_DIR + "/" + self.testdir
        sshserver.ssh_exec("rm -fr {0}&&mkdir -p {0}".format(self.testpath))
        # 增加quota命令
        self.add_quota = self.get_cli(self, "noquota_add_ignore", self.testdir, "10T", 500000) + \
                         " > /tmp/autotest_quota.log 2>&1 &"
        self.del_quota = self.get_cli(self, "quota_remove", self.testdir)
        self.list_quota = self.get_cli(self, "quota_list_verbose", self.testdir)
        # 检查客户java工具是否安装,如果不存在尝试安装
        java_stat, _ = sshclient.ssh_exec("java -version")
        if java_stat != 0:
            ins_stat, _ = sshclient.ssh_exec("yum -y install java")
            if ins_stat != 0:
                logger.error("java not install in this node,test will skip.")
                pytest.skip(msg="not found java jdk,test skip.")
        # 检查vdbench测试工具是否存在
        vd_stat, _ = sshclient.ssh_exec("/opt/vdbench547/vdbench -t")
        if vd_stat != 0:
            sshsftp.sftp_upload("tools/vdbench547.tar.gz", "/opt/vdbench547.tar.gz")
            sshclient.ssh_exec("tar -zxvf /opt/vdbench547.tar.gz -C /opt")
        # 客户端挂载

        sshserver.ssh_exec(self.get_cli(self, "acl_ip_add", self.testdir, "*", "rw"))
        mount_stat = client_mount(self.clientip, subdir=self.testdir)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed,test skip.")
        # 客户端vdbench写入十万数据
        vdbench_config = "messagescan=no\n" \
                         "fsd=fsd1,anchor=/mnt/yrfs,depth=1,width=5,files=20000,size=4K,shared=yes\n" \
                         "fwd=default,xfersize=4K,fileio=sequential,fileselect=sequential,operation=create,threads=4\n" \
                         "fwd=fwd1,fsd=fsd1\n" \
                         "rd=rd1,fwd=fwd*,fwdrate=max,format=restart,elapsed=40,interval=20"
        create_stat = sshsftp.sftp_createfile("/opt/auotest_quota_falut", content=vdbench_config)
        assert create_stat == 0, "sftp create file failed."

        logger.info("vdbench running.")
        vd_stat, _ = sshclient.ssh_exec("/opt/vdbench547/vdbench -f /opt/auotest_quota_falut")
        assert vd_stat == 0, "vdbench create failed."
        sshserver.close_connect()
        sshclient.close_connect()
        sshsftp.close_connect()

    def teardown_class(self):
        sshserver = sshClient(self.serverip)
        # 清理数据文件，删除测试目录，删除acl
        sshserver.ssh_exec(self.get_cli(self, "acl_ip_del", self.testdir, "*"))
        # 清理测试数据
        sshserver.ssh_exec("mkdir -p %s/autotest_del" % consts.MOUNT_DIR)
        del_stat, _ = sshserver.ssh_exec("rsync -avpgolr --progress --delete /mnt/yrfs/autotest_del/ "
                                              "/mnt/yrfs/auotest_quota_falut/")
        assert del_stat == 0, "delete file failed."
        sshserver.ssh_exec("rm -fr /mnt/yrfs/autotest_del /mnt/yrfs/auotest_quota_falut")
        sshserver.close_connect()

    def setup(self):
        self.newfault = makeFault()
        self.sshserver = sshClient(self.serverip)

    def teardown(self):
        self.sshserver.ssh_exec(self.del_quota)
        # self.sshserver.ssh_exec("cat /tmp/autotest_quota.log")
        self.sshserver.ssh_exec("rm -fr /tmp/autotest_quota.log")
        self.sshserver.close_connect()

    def test_oss_fault(self):
        """
        3686 （非空目录quota）设置中oss服务故障测试
        """
        logger.info("[non-empty dir set quota oss fault] running.")
        try:
            # 设置quota过程中
            self.sshserver.ssh_exec(self.add_quota)
            sleep(1)
            # 故障oss master服务
            self.newfault.kill_oss(check=False)
            # 故障恢复后查询quota信息是否正确
            for i in range(360):
                stat, _ = self.sshserver.ssh_exec("ps axu|grep \"yrcli --projectquota\"|grep -v grep")
                if stat == 0:
                    logger.info("waiting projectquota process exit.")
                    sleep(10)
                    continue
                else:
                    logger.info("%s, process exit" % self.add_quota)
                    break

            stat, res = self.sshserver.ssh_exec(self.list_quota)
            res = res.split("\n")[2]
            spaceused = res.split()[2]
            inodeused = res.split()[4]
            opstatus = res.split()[7]
            assert spaceused == "391MiB"
            assert inodeused == "100007"
            assert opstatus == "finished"
        finally:
            self.sshserver.ssh_exec(self.del_quota)
            check_cluster_health()

    def test_mds_fault(self):
        """
        3687 （非空目录quota）设置中mds服务故障测试
        """
        logger.info("[non-empty dir set quota mds fault] running.")
        try:
            # 设置quota过程中
            self.sshserver.ssh_exec(self.add_quota)
            sleep(1)
            # 故障mds master服务
            self.newfault.kill_meta(check=False)
            # 故障恢复后查询quota信息是否正确
            while True:
                stat, _ = self.sshserver.ssh_exec("ps axu|grep \"yrcli --projectquota\"|grep -v grep")
                if stat == 0:
                    logger.info("waiting projectquota process exit.")
                    sleep(10)
                    continue
                else:
                    logger.info("%s, process exit" % self.add_quota)
                    break

            stat, res = self.sshserver.ssh_exec(self.list_quota)
            res = res.split("\n")[2]
            spaceused = res.split()[2]
            inodeused = res.split()[4]
            opstatus = res.split()[7]
            assert spaceused != "0.0B"
            assert int(inodeused) > 0
            assert opstatus == "finished"
        finally:
            self.sshserver.ssh_exec(self.del_quota)
            check_cluster_health()

    def test_mgr_fault(self):
        """
        3688 （非空目录quota）设置中mgr服务故障测试
        """
        logger.info("[non-empty dir set quota mgr fault] running.")
        # 设置quota过程中
        try:
            self.sshserver.ssh_exec(self.add_quota)
            sleep(1)
            # 故障mds master服务
            self.newfault.kill_mgr()
            # 故障恢复后查询quota信息是否正确
            while True:
                stat, _ = self.sshserver.ssh_exec("ps axu|grep \"yrcli --projectquota\"|grep -v grep")
                if stat == 0:
                    logger.info("waiting projectquota process exit.")
                    sleep(10)
                    continue
                else:
                    logger.info("%s, process exit" % self.add_quota)
                    break

            stat, res = self.sshserver.ssh_exec(self.list_quota)
            res = res.split("\n")[2]
            spaceused = res.split()[2]
            inodeused = res.split()[4]
            opstatus = res.split()[7]
            assert spaceused == "391MiB"
            assert inodeused == "100007"
            assert opstatus == "finished"
        finally:
            self.sshserver.ssh_exec(self.del_quota)
            check_cluster_health()
