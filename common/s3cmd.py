#!/usr/bin/env python
# -*- coding:utf-8 -*-

import boto
import boto.s3.connection
from config import consts
import logging
import traceback

logger = logging.getLogger(__name__)

class S3Object():

    def __init__(self, HOST=None,
                    PORT=None,
                    access_key=None,
                    secret_key=None,
                    bucket=None):
        if not HOST:
            HOST = consts.s3["hostname"].split(":")[0]

        if not PORT:
            PORT = int(consts.s3["hostname"].split(":")[1])

        if not access_key:
            access_key = consts.s3["access_key"]

        if not secret_key:
            secret_key = consts.s3["secret_access_key"]

        if not bucket:
            self.bucket = consts.s3["bucketname"]
        else:
            self.bucket = bucket

        try:
            self.conn = boto.connect_s3(
                aws_access_key_id = access_key,
                aws_secret_access_key = secret_key,
                host = HOST,
                port = PORT,
                is_secure = False,
                calling_format = boto.s3.connection.OrdinaryCallingFormat()
            )
            logger.info("S3 server: %s port: %s Connected" % (HOST, PORT))
        except Exception as e:
            logger.error(traceback.format_exc(e))

    def get_keys(self):
        try:
            tt = self.conn.get_bucket(self.bucket)
            keys_len = len(tt.get_all_keys())
            logger.info("Get bucket %s keys: %s." % (self.bucket, keys_len))

            return keys_len
        except Exception as e:
            logger.error(traceback.format_exc(e))


