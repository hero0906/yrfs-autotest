#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Desciption : nfs case depend
@Time : 2021/11/17 14:55
@Author : caoyi
"""
import logging
from common.restrequest import RestRequest

logger = logging.getLogger(__name__)


class NfsRest(RestRequest):
    def __init__(self):
        super().__init__()
        self.dns_sys_uri = "/sysconfig"
        self.share_uri = "/shares"
        self.target_uri = "/targets"

    def get_dns_name(self):
        """
        :return:
        """
        stat, res = self.get(self.dns_sys_uri)
        if stat == 200:
            dns_name = res["dns_name"]
            logger.info("Dns domain: %s." % dns_name)
            return "nfs." + dns_name
        else:
            logger.error("Not found dns config.")
            return None

    def get_dns_ip(self):
        stat, res = self.get(self.dns_sys_uri)
        if stat == 200:
            #dns master slave ip获取
            dns_master_ip = res["dns_master_ip"]
            dns_slave_ip = res["dns_slave_ip"]
            logger.info("Dns master ip: %s, slave ip: %s" % (dns_master_ip, dns_slave_ip))
            return (dns_master_ip, dns_slave_ip)
        else:
            logger.error("Not found dns ip")
            return None

    def add_share(self, testdir, rpermiss="no_root_squash",
                  permiss="no_all_squash", wmode="sync", mode="rw", target="*"):
        """
        :param testdir:
        :param rpermiss:
        :param permiss:
        :param wmode:
        :param mode:
        :param target:
        :return:
        """
        # 创建nfs share
        add_shares = {"shares": {}}
        add_shares["shares"]["name"] = "auotest_nfs_share"
        add_shares["shares"]["path"] = "/" + testdir
        add_shares["shares"]["share_type"] = "NFS"
        stat, res = self.post(self.share_uri, add_shares)
        if stat == 200:
            share_id = res["share"]["id"]
            logger.info("Share dir: % share id: %s" % (testdir, share_id))
        else:
            logger.error("Add share dir %s failed." % testdir)
            assert False
        # 添加acl权限
        post_acl = {"target": {"extra": {}}}
        post_acl["target"]["share_id"] = share_id
        post_acl["target"]["extra"]["root_permissions"] = rpermiss
        post_acl["target"]["extra"]["write_mode"] = wmode
        post_acl["target"]["extra"]["permissions"] = permiss
        post_acl["target"]["target"] = target
        post_acl["target"]["mode"] = mode
        post_acl["target"]["target_type"] = "ip"
        stat, res = self.post(self.target_uri, post_acl)
        if stat == 200:
            target_id = res["target"]["id"]
            logger.info("Add share dir %s permission" % testdir)
        else:
            logger.error("Add dir %s permission Failed." % testdir)
            assert False
        # #获取nfs配置id
        # stat, res = self.get(self.acl_uri + "?share_id=" + share_id)
        # if stat == 200:
        #     nfs_id = res["targets"][0]["id"]
        #     logger.info("Get nfs dir %s id: %s" % (testdir, nfs_id))
        # else:
        #     logger.error("Get dir %s id failed." % testdir)
        return target_id, share_id

    def update_share(self, target_id, rpermiss="no_root_squash",
                     permiss="no_all_squash", wmode="sync", mode="rw"):
        """
        :param share_id:
        :param rpermiss:
        :param permiss:
        :param wmode:
        :param mode:
        :return:
        """
        uri = self.target_uri + "/" + target_id
        post_acl = {"target": {"extra": {}}}
        post_acl["target"]["extra"]["root_permissions"] = rpermiss
        post_acl["target"]["extra"]["write_mode"] = wmode
        post_acl["target"]["extra"]["permissions"] = permiss
        post_acl["target"]["mode"] = mode
        stat, _ = self.put(uri, post_acl)
        if stat == 200:
            logger.info("Update nfs share.")
            return True
        else:
            logger.error("Update nfs failed.")
            return False

    def del_share(self, target_id, share_id):
        """
        :param target_id:
        :return:
        """
        share_uri = self.share_uri + "/" + share_id
        target_uri = self.target_uri + "/" + target_id
        # 删除共享权限
        stat, _ = self.delete(target_uri)
        stat2, _ = self.delete(share_uri)
        if stat == 202 and stat2 == 202:
            logger.info("Delete target and share success")
            return True
        else:
            logger.error("Delete target and share failed.")
            return False
