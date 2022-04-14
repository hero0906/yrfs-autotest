#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pytest
from time import sleep
from uuid import uuid4
from common.restrequest import RestRequest
from common.util import sshClient
from config import consts

@pytest.mark.skip
@pytest.mark.funcTest
class Test_nfsApi():

    def setup_class(self):
        #获取token
        self.nfsrest = RestRequest()
        self.groups_api = "/groups"
        self.users_api = "/users"
        self.mountdir = consts.MOUNT_DIR
        self.serverip = consts.META1
        self.sshserver = sshClient(self.serverip)

    def teardown_class(self):
        self.sshserver.close_connect()

    def test_create_group(self):
        """
        3431 创建本地用户组
        3436 (自动化)创建本地用户
        3447 (自动化)删除本地用户
        3446 修改本地用户的属组
        """
        #创建组
        primary_group_name = "autotest_nfs_group_" + str(uuid4())[:5]
        group_name = "autotest_nfs_group_" + str(uuid4())[:5]
        user_name = "autotest_nfs_user_" + str(uuid4())[:5]
        for i in (primary_group_name, group_name):
            body = {
                "group": {
                "name": i,
                "description": "autotest nfs create"
                }
            }
            stat, res = self.nfsrest.post(self.groups_api, body)
            assert stat == 200, "Expect create group success."

            stat_err, _ = self.nfsrest.post(self.groups_api, body)
            assert stat_err == 400, "Expect create group failed."

            if i == primary_group_name:
                primary_group_id = res["group"]["id"]
            else:
                group_id = res["group"]["id"]
        #获取用户组
        stat, res = self.nfsrest.get(self.groups_api + "/" + primary_group_id)
        assert res["group"]["name"] == primary_group_name and stat == 200, "Expect get group failed."
        #后台检验用户组
        sleep(10)
        stat, _ = self.sshserver.ssh_exec("cat /etc/group|grep " + primary_group_name)
        # assert stat == 0, "Expect create group success."
        #创建用户
        body = {
            "user":{
                "name": user_name,
                "gr_name": primary_group_name,
                "passwd": "Passw0rd@123",
                "description": "autotest create"
            }
        }
        stat, res = self.nfsrest.post(self.users_api, body)
        assert stat == 200, "Expect create group success."
        user_id = res["user"]["id"]
        #再次创建同名用户失败
        stat, _ = self.nfsrest.post(self.users_api, body)
        assert stat == 400, "Expect create group failed."
        #获取用户
        stat, res = self.nfsrest.get(self.users_api + "/" + user_id)
        assert res["user"]["name"] == user_name and stat == 200, "Expect get user failed."
        #后台检验用户创建成功
        sleep(10)
        stat, _ = self.sshserver.ssh_exec("cat /etc/passwd|grep " + user_name)
        # assert stat == 0, "Expect create user success."
        #更新本地用户的附属组
        body = {
            "user":{
                "passwd": "Passw0rd@123",
                "description": "test group update",
                "gr_nam": primary_group_name,
                "groups": [group_name]
            }
        }
        stat, res = self.nfsrest.put(self.users_api + "/" + user_id, body)
        assert stat == 200, "Expect update group success."
        #删除附属组
        stat, res = self.nfsrest.delete(self.groups_api + "/" + group_id)
        assert stat == 202, "Expect del group success."
        #删除用户
        stat, res = self.nfsrest.delete(self.users_api + "/" + user_id)
        assert stat == 202, "Expect del user success."
        # sleep(10)
        # stat, _ = self.sshserver.ssh_exec("cat /etc/passwd|grep " + user_name)
        # assert stat != 0, "Expect del user success."
        #删除用户组
        stat, res = self.nfsrest.delete(self.groups_api + "/" + primary_group_id)
        assert stat == 202, "Expect del group success."
        # sleep(10)
        # stat, _ = self.sshserver.ssh_exec("cat /etc/group|grep " + primary_group_name)
        # assert stat != 0, "Expect del group success."
