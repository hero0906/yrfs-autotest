#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Desciption : test kernel compatible suite
@Time : 2021/11/08 15:13
@Author : caoyi
"""
import pytest
import logging
from common.util import sshClient, sshSftp, ping_test
from time import sleep
from config import consts
from depend.client import client_mount, run_fstest

logger = logging.getLogger(__name__)
# 以下版本内核的兼容性测试
kernel_versions = ("3.10.0-327",
                   "3.10.0-693",
                   "3.10.0-957",
                   "4.4.229",
                   "4.19.13"
                   )


@pytest.mark.skip
@pytest.mark.serviceTest
class Test_kernel:

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        sshclient = sshClient(self.clientip)
        # 备份当前内核配置
        sshclient.ssh_exec("\\cp /boot/grub2/grubenv /boot/grub2/grubenv.bak")
        sshclient.close_connect()

    def teardown_class(self):
        # 恢复环境
        sshclient = sshClient(self.clientip)
        sshclient.ssh_exec("\\cp /boot/grub2/grubenv.bak /boot/grub2/grubenv")
        sshclient.ssh_exec("reboot -f", timeout=1)
        sleep(10)
        for i in range(60):
            stat = ping_test(self.clientip)
            if not stat:
                logger.warning("Client Network unreachable,sleep 10")
                sleep(10)
                continue
            else:
                break
        else:
            raise ValueError("client boot failed")

    def setup(self):
        self.sshclient = sshClient(self.clientip)
        self.sshsftp = sshSftp(self.clientip)

    @pytest.mark.parametrize("kernel_ver", kernel_versions)
    def test_kernel_compat(self, kernel_ver):
        # 查看内核是否安装
        stat, _ = self.sshclient.ssh_exec(
            "awk -F\\' '$1==\"menuentry \" {print $2}' /etc/grub2.cfg|grep %s" % kernel_ver)
        if stat != 0:
            self.sshsftp.sftp_upload("tools/kernel/%s.tar.gz" % kernel_ver, "/tmp/%s.tar.gz" % kernel_ver)
            self.sshclient.ssh_exec("tar -zxvf /tmp/{0}.tar.gz -C /tmp&&rpm -ivh /tmp/{0}/kernel*.rpm \
                                    --nodeps --force".format(kernel_ver))
        # 切换内核
        self.sshclient.ssh_exec("grub2-mkconfig -o /boot/grub2/grub.cfg")
        stat, res = self.sshclient.ssh_exec(
            "awk -F\\' '$1==\"menuentry \" {print $2}' /etc/grub2.cfg|grep %s" % kernel_ver)
        assert stat == 0, "not found kernel rpm"
        self.sshclient.ssh_exec('sed -i "s/^saved_entry.*/saved_entry=%s/g" /boot/grub2/grubenv' % res)
        # 系统重启
        self.sshclient.ssh_exec("reboot -f", timeout=1)
        sleep(10)
        for i in range(60):
            sleep(5)
            stat = ping_test(self.clientip)
            if not stat:
                logger.warning("Client Network unreachable,sleep 10")
                sleep(10)
                continue
            else:
                break
        else:
            raise ValueError("client boot failed")
        # 执行fstest
        mount_stat = client_mount(self.clientip, acl_add=True)
        assert mount_stat == 0, "client mount failed."
        run_fstest(self.clientip, consts.MOUNT_DIR)
