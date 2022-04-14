#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : win client case suite
@Time : 2021/09/13 10:57
@Author : caoyi
"""

import pytest
from common.util import sshClient
from depend.client import win_client_mount
from config import consts


class Test_winClient:
    def setup_class(self):
        self.client = consts.WINCLIENT
        self.server = consts.META1
        self.sshclient = sshClient(self.client, linux=False)
        self.sshserver = sshClient(self.server)

    @pytest.mark.parametrize("cache", ("open", "close"))
    def test_no_app_cache(self, cache):
        """
        3546 不开启application meta cache配置,打开系统缓存与关闭挂载正确
        """
        if cache == "open":
            stat = win_client_mount(self.client, drivercache="true", acl_add=True)
        else:
            stat = win_client_mount(self.client, acl_add=True)

        assert stat == 0, "Expect: client mount success."
