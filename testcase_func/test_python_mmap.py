# coding=utf-8
"""
@Desciption : s3 tiering case
@Time : 2020/5/27 18:47
@Author : caoyi
"""

import pytest
import logging
from time import sleep
from config import consts
from common.util import sshClient
from depend.client import client_mount
from common.cli import YrfsCli


class TestpythonMamp(YrfsCli):

    def setup_class(self):
        self.clientip = consts.CLIENT[0]
        serverip = consts.META1
        self.sshserver = sshClient(serverip)
        #客户端挂载
        self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_add", "", "*", "rw"))
        mount_stat = client_mount(self.clientip)
        if mount_stat != 0:
            pytest.skip(msg="client mount failed, test skip.")

        self.sshserver = sshClient(serverip)
        self.sshclient = sshClient(self.clientip)
        #检查客户端是否存在mmap模块
        import_stat, _ = self.sshclient.ssh_exec("python -c \"import mmap\"")
        if import_stat != 0:
           pytest.skip(msg="client need import mmap")

        self.testpath = consts.MOUNT_DIR + "/" + "autotest_python_mmap"

    def teardown_class(self):
        self.sshserver.ssh_exec(self.get_cli(self, "acl_ip_del", "", "*"))
        self.sshclient.close_connect()
        self.sshserver.close_connect()

    def test_python_mmap(self):
        '''
        创建两个线程，一个线程把文件用mmap映射到内存。另一个线程 做正常的open close.
        预期读数据都正常， 内核不会crash.
        '''
        #创建文件
        self.sshclient.ssh_exec("echo -e \"test python mmap by caoyi\" > %s" % self.testpath)
        _, md5_1 = self.sshclient.ssh_exec("md5sum " + self.testpath)
        #拷贝测试脚本到远程
        autotest_mmap = "\nimport mmap\n" \
                        "import time\n" \
                        "with open ('{}', 'rb') as f:\n".format(self.testpath) + \
                        "\tmm = mmap.mmap(f.fileno(), 0)\n" \
                        "\tmm.readline()\n" \
                        "\ttime.sleep(5)\n" \
                        "\tmm.close()"
        autotest_open = "\nimport time\n"\
                        "with open ('{}', 'rb') as f:\n".format(self.testpath) + \
                        "\tf.readline()\n" \
                        "\ttime.sleep(5)\n" \
                        "\tf.close()"
        self.sshclient.ssh_exec("echo -e \"%s\" > /tmp/autotest_mmap.py&&python /tmp/autotest_mmap.py &" % autotest_mmap)

        open_stat, _ = self.sshclient.ssh_exec("echo -e \"%s\" > /tmp/autotest_open.py&&python /tmp/autotest_open.py" \
                                               % autotest_open)

        assert open_stat == 0,"test open file failed."
        sleep(2)
        #校验两次md5值是否一致
        _, md5_2 = self.sshclient.ssh_exec("md5sum " + self.testpath)
        assert md5_1 == md5_2, "md5sum failed."
        #测试删除文件是否成功
        del_stat, _ = self.sshclient.ssh_exec("rm -fr /tmp/autotest_open.py /tmp/autotest_mmap.py")
        assert del_stat == 0, "del file failed."
        del_file, _ = self.sshclient.ssh_exec("rm -fr " + self.testpath)
        assert del_file == 0,"del test file failed."