# coding=utf-8
"""
@Desciption : test getsla.
@Time : 2021/03/23 14:44
@Author : caoyi
"""

import pytest
from common.cli import YrfsCli
from config import consts
from common.util import sshClient


@pytest.mark.smokeTest
class Testsla(YrfsCli):
    """
    test cli get sla
    """

    def test_getsla(self):
        """
        bugID: 3846 【6.5.3】【ipv6】执行yrcli --getsla出现coredump SIGABRT异常终止。
        """
        serverip = consts.META1
        sshserver = sshClient(serverip)
        try:
            stat, _ = sshserver.ssh_exec(self.get_cli("get_sla"))
            assert stat == 0, "get sla info success."
        finally:
            sshserver.close_connect()