#!/usr/bin/env python
# -*- coding:utf-8 -*-

import boto3
import os
from botocore.client import Config
from config import consts
import logging


logger = logging.getLogger(__name__)

class S3Object():

    def __init__(self, endpoint=None,
                    access_key=None, secret_key=None,
                    bucket=None, push_point=None, region='default'):
        if not endpoint:
            self.endpoint = "http://" + consts.s3["hostname"]
        else:
            self.endpoint = "http://" + endpoint

        if not access_key:
            self.access_key = consts.s3["access_key"]
        else:
            self.access_key = access_key

        if not secret_key:
            self.secret_key = consts.s3["secret_access_key"]
        else:
            self.secret_key = secret_key

        if not bucket:
            self.bucket = consts.s3["bucketname"]
        else:
            self.bucket = bucket

        if not push_point:
            self.push_point = "http://" + consts.SUBSCRIBE_ENDPOINT
        else:
            self.push_point = "http://" + push_point

        self.region = region

    def _conn_server(self, messtype):
        if messtype in ("s3", "sns"):
            logger.info("s3 connect type: %s" % messtype)
        else:
            logger.error("connect type: %s not found" % messtype)
            raise ValueError
        try:
            conn = boto3.client(messtype, self.region, use_ssl=False, verify=False,
                            aws_access_key_id=self.access_key,
                            aws_secret_access_key=self.secret_key,
                            endpoint_url=self.endpoint,
                            config=Config(signature_version='s3'))
            logger.info("s3 server: %s, connected." % (self.endpoint))
            return conn
        except Exception as e:
            logger.error(e)

    def get_keys(self, content=False):
        conn = self._conn_server("s3")
        res = conn.list_objects(Bucket=self.bucket)
        if res["ResponseMetadata"]["HTTPStatusCode"] == 200:
            if "Contents" not in res.keys():
                logger.info("bucket: %s is null" % self.bucket)
                return 0
            else:
                if content:
                    keys_list = []
                    for key in res["Contents"]:
                        keys_list.append(key["Key"])
                    logger.info("bucket: %s, keys:%s." % (self.bucket, keys_list))
                    return keys_list
                else:
                    keys = len(res["Contents"])
                    logger.info("bucket: %s key numbers: %s" % (self.bucket, keys))
                    return keys
        else:
            logger.error("get bucket:%s keys failed." % (self.bucket))
            return 0

    def create_topic(self, topic_name="autotest-cytopic001"):

        conn = self._conn_server("sns")
        res = conn.create_topic(Name=topic_name,
                        Attributes={"push-endpoint": self.push_point,
                                    "use-ssl": "false", "verify-ssl":"false"})
        if res["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info("created topic,name: %s" % topic_name)
        else:
            logger.error("create topic failed,name: %s" % topic_name)

    def put_bucket_notify(self, Id="autotest-cynotif001",
                          topic_name="autotest-cytopic001", prefix="autotest"):
        conf = {'TopicConfigurations': [{
                'Id': Id,
                'TopicArn': 'arn:aws:sns:default::' + topic_name,
                'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*'],
                'Filter': {'Key':{
                    'FilterRules': [{
                            'Name': 'prefix',
                            'Value': prefix}
                    ]}}}]}
        conn = self._conn_server("s3")
        res = conn.put_bucket_notification_configuration(Bucket=self.bucket, NotificationConfiguration=conf)
        if res["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info("put notification,Id:%s, name:%s, prefix:%s,done." % (Id, topic_name, prefix))
        else:
            logger.error("put notification error,Id:%s, name:%s, prefix:%s." % (Id, topic_name, prefix))

    def create_topic_notify(self,Id="autotest-cynotif3000",
                            topic_name="autotest-cytopic5100",prefix="autotest"):
        Id = Id
        topic_name = topic_name
        prefix = prefix
        self.create_topic(topic_name)
        self.put_bucket_notify(Id, topic_name, prefix)

    def upload(self, filepath):
        conn = self._conn_server("s3")
        try:
            if os.path.isfile(filepath):
                key_name = filepath.split("/")[-1]
                conn.upload_file(Filename=filepath,Bucket=self.bucket,Key=key_name)
                logger.info("upload {} to {} done!".format(filepath, self.bucket))
            elif os.path.isdir(filepath):
                for o,p,q in os.walk(filepath):
                    if q:
                        for f in q:
                            filename = os.path.join(o,f)
                            conn.upload_file(Filename=filename, Bucket='testcao001', Key=f)
                            logger.info("upload {}, key {}, to {} done!".format(filename, f, self.bucket))
            else:
                logger.error("file %s not found." % filepath)
        except Exception as e:
            logger.error("upload {} error: {}".format(filepath, e))

    def bucket_clean(self, key_name=None):
        conn = self._conn_server("s3")
        objects = conn.list_objects(Bucket=self.bucket)
        if "Contents" not in objects.keys():
            logger.info("bucket: %s clear." % self.bucket)
            return
        if key_name:
            #res = conn.delete_objects(Bucket=self.bucket,Delete={'Objects': [{'Key': key_name}]})
            res = conn.delete_object(Bucket=self.bucket, Key=key_name)
            if res["ResponseMetadata"]["HTTPStatusCode"] == 204:
                logger.info("delete objcet %s done." % key_name)
            else:
                logger.error("delete object %s error, %s." % (key_name, res))
        else:
            for obj in objects['Contents']:
                obj_key = obj['Key']
                res = conn.delete_object(Bucket=self.bucket, Key=obj_key)
                if res["ResponseMetadata"]["HTTPStatusCode"] == 204:
                    logger.info("delete objcet %s done." % obj_key)
                else:
                    logger.error("delete object %s error, %s." % (obj_key, res))