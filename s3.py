#!/usr/bin/env python
# -*- coding:utf-8 -*-
import boto
import boto.s3.connection
access_key = 'minioadmin'
secret_key = 'minioadmin'
host = "192.168.0.40"
port = 9000

conn = boto.connect_s3(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        host = host,
        port=port,
        is_secure=False,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

bucket = conn.get_all_buckets()
b = conn.get_bucket('testcao1')
for i in dir(b):
    print(i)
t = b.get_all_keys()
print(t)
