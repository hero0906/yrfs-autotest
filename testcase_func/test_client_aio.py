# coding=utf-8
"""
@Desciption : client steady test
@Time : 2020/03/18 19:02
@Author : caoyi
"""

import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient
from depend.client import client_mount


@pytest.mark.funcTest
class Test_aiohung(YrfsCli):
    """
    客户端稳定性case集合
    """

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        self.serverip = consts.META1

    def test_aio_hung(self):
        """
        bugID:4153 aio模式中，bs为2M，然后iodepth设置到128，理论上可能会触发内存的hung
        """
        sshclient = sshClient(self.clientip)
        sshserver = sshClient(self.serverip)
        acl_id = "autotestaio"
        testfile = consts.MOUNT_DIR + "/autotest_aiohung"
        try:
            # 客户端挂载
            sshserver.ssh_exec(self.get_cli("acl_id_add", "", acl_id, "rw"))
            mount_stat = client_mount(self.clientip, aclid=acl_id)
            # 开启aio模式
            set_aio_stat, _ = sshclient.ssh_exec("echo 1 > aio_enable")

            fio_cmd = "fio -iodepth=128 -numjobs=2 -size=1G -ramp_time=0 -time_based -runtime=120 -ioengine=libaio " + \
                      "-bs=2m -name=test -filename=%s" % testfile
            fio_stat, _ = sshclient.ssh_exec(fio_cmd)
            # 校验点
            assert mount_stat == 0, "client mount failed."
            assert set_aio_stat == 0, "set aio mode failed."
            assert fio_stat == 0, "fio run failed."
        finally:
            # 环境清理
            sshserver.ssh_exec(self.get_cli("acl_id_del", "", acl_id))
            sshserver.ssh_exec("rm -fr " + testfile)
            sshclient.close_connect()
            sshserver.close_connect()
