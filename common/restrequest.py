#!/usr/bin/env python
# -*- coding:utf-8 -*-

import http.client as httplib
from config import consts
from common.util import sshClient
import logging
import re
import traceback
import simplejson

logger = logging.getLogger(__name__)


class RestException(Exception):
    pass


def _get_token():
    ssh = None
    authtoken = ""
    projid = ""
    try:
        ssh = sshClient(consts.META1)
        _, res = ssh.ssh_exec("source /root/.openrc;openstack token issue")
        projid = re.findall(r"project_id.*? ([0-9A-Za-z].*[0-9A-Za-z])", res)
        authtoken = re.findall(r" id.*? ([a-zA-Z].*) .*?", res, re.M)
        logger.info("Get Token: %s, Prject_id: %s" % (authtoken, projid))
    except Exception as e:
        logger.error("Exception: %s" % e)
    finally:
        ssh.close_connect()
    return "".join(authtoken), "".join(projid)


class RestRequest():
    def __init__(self):
        self.host = consts.META1
        self.port = consts.NFS_PORT
        get_token = _get_token()
        self.authtoken = get_token[0]
        self.projid = get_token[1]

    def _build_header(self):
        headers = {"Content-Type": "application/json",
                   "X-Auth-Token": "%s" % self.authtoken}

        return headers

    def _send_request(self, uri, method, body, token):
        global status, result
        if not uri:
            logger.error("uri not found")
            raise RestException()
        uri = "/v2/" + self.projid + uri
        conn = None
        try:
            conn = httplib.HTTPConnection(self.host, self.port)
            logger.info("connect http server %s." % self.host)
            if token:
                self.headers["Cookie"] = token
            logger.info("method: %s, uri: %s, body: %s." % (method, uri, body))
            if body:
                body = simplejson.dumps(body)

            conn.request(method, uri, body, self._build_header())
            response = conn.getresponse()
            status = response.status
            result = response.read().decode()
            #转换为字典
            if result:
                result = simplejson.loads(result)
            logger.info("status: %s, result: %s" % (status, result))
        except Exception as e:
            logger.error("Exception: %s" % traceback.format_exc(e))
        finally:
            if conn:
                logger.info("Close http connect.")
                conn.close()
        return status, result

    def get(self, uri, body="", token=None):
        return self._send_request(uri, "GET", body=body, token=token)

    def post(self, uri, body="", token=None):
        return self._send_request(uri, "POST", body=body, token=token)

    def put(self, uri, body="", token=None):
        return self._send_request(uri, "PUT", body=body, token=token)

    def delete(self, uri, body="", token=None):
        return self._send_request(uri, "DELETE", body=body, token=token)