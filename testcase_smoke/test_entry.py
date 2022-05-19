# coding=utf-8
"""
@Desciption : yrcli entry relate case
@Time : 2020/03/18 16:00
@Author : caoyi
"""

import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.skip_mark import verify_mount_point
from common.cluster import get_entry_info, get_Cluster_Hostip

yrfs_version = consts.YRFS_VERSION

# pytest.mark.skipif(verify_mount_point() != 0, reason="server yrfs mount point not exist")
@pytest.mark.smokeTest
class TestEntry(YrfsCli):

    def setup_class(self):
        if verify_mount_point() != 0:
            pytest.skip(msg="server yrfs mount point not exist", allow_module_level=True)
        self.serverip = consts.META1

    def test_get_entry(self):
        """
        bugID: 4160 yrcli --getentry osd info显示不全
        """
        testfile = "autotest_getentry"
        testpath = consts.MOUNT_DIR + "/" + testfile

        sshserver = sshClient(self.serverip)
        sshserver.ssh_exec("touch " + testpath)
        _, file_info = sshserver.ssh_exec(self.get_cli("get_entry", testfile))

        sshserver.ssh_exec("rm -fr " + testpath)
        sshserver.close_connect()

        assert "Data Redundancy: Mirror" in file_info, "match error"
        assert "Meta Redundancy: Mirror" in file_info, "match error"
        assert "Stripe Size" in file_info, "match error"

    #@pytest.mark.skipif(int(yrfs_version) >= 664, reason="664 no need to execute")
    def test_readinode_attr(self):
        """
        3379 yrcli --readinode获取inode扩展属性信息
        """
        sshmaster = ""
        testdir = "autotest_readinode"
        mountdir = consts.MOUNT_DIR
        serverip = consts.META1
        readinode = "yrcli --readinode --path={}"
        # 创建测试文件
        sshserver = sshClient(serverip)
        inode_dict = {}
        try:
            # 测试文件创建
            sshserver.ssh_exec("cd %s&&mkdir %s" % (mountdir, testdir))
            sshserver.ssh_exec("cd {0}&&cd {1}&&touch {1}_file".format(mountdir, testdir))
            sshserver.ssh_exec("cd {0}&&cd {1}&&mkdir {1}_dir".format(mountdir, testdir))
            # 获取文件所在entry信息
            entry_info = get_entry_info(testdir)
            inode_path = entry_info["Inode hash path"]
            node_name = entry_info["nodename"]
            # 获取master管理ip
            hostip = get_Cluster_Hostip()
            masterip = hostip[node_name][1]
            # 查找到inode entry的完全路径
            sshmaster = sshClient(masterip)
            _, res = sshmaster.ssh_exec("ls /data/mds*/replica/inodes/" + inode_path)
            stat, res = sshmaster.ssh_exec(readinode.format(res))
            assert stat == 0, "readinode failed."
            for i in res.split("\n"):
                i = i.split(":")
                inode_dict[i[0]] = i[1].strip()
            assert inode_dict["metaType"] == "dir"
            assert inode_dict["numFiles"] == "1"
            keys = [i for i in inode_dict.keys()]
            assert "formatVer" in keys
            assert "fetureflags" in keys
            assert "meta.flags" in keys
            assert "meta.mode" in keys
            assert "meta.userid" in keys
            assert "meta.groupid" in keys
            assert "meta.bTime" in keys
            assert "stripeType" in keys
            assert "eid" in keys
            assert "stripeSize" in keys
            assert inode_dict["numSubdirs"] == "1"

        finally:
            sshserver.ssh_exec("cd %s&&rm -fr %s" % (mountdir, testdir))
            sshserver.close_connect()
            sshmaster.close_connect()
