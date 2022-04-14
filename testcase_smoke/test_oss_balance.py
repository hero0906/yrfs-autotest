# coding=utf-8

"""
@Desciption : oss balance
@Time : 2020/12/11 18:58
@Author : caoyi
"""
import pytest
from common.cli import YrfsCli
from common.util import ssh_exec
from config import consts

ip = consts.META1


@pytest.mark.smokeTest
class Test_oss_balance(YrfsCli):

    def test_oss_snap_recover(self):
        """
        # caseID: 2567 osd快照手动创建后恢复验证
        """
        osd_map_cmd = self.get_cli('osd_map')
        osd_map1 = ssh_exec(ip, osd_map_cmd)
        create_snap_res = ssh_exec(ip, self.get_cli('create_osd_snap'))
        assert 'snapshot ok' in create_snap_res
        balance_res = ssh_exec(ip, self.get_cli('osd_snap_recover'))
        assert "balance request sent" in balance_res
        osd_map2 = ssh_exec(ip, osd_map_cmd)
        assert osd_map1 == osd_map2
