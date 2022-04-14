# -*- coding:utf-8 -*-
from time import sleep
# import sys
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from script.feishu import FeiShutalkChatbot
from common.util import sshClient

webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/da08a6da-fd84-4467-916e-29f218a0dfd8"
secret = "t2rkH3clSpzq31u6Ot4Uld"

feishu = FeiShutalkChatbot(webhook, secret=secret)
ssh = sshClient("10.16.2.18")
while True:
    stat, _ = ssh.ssh_exec("ps axu|grep -v grep|grep runner.py")
    if stat == 0:
        log = "logs/autotest.log"
        _, content = ssh.ssh_exec("tail -n 1 " + log)
        print(content)
        feishu.send_text("".join(content))
        print("sleep 300")
        sleep(300)
    else:
        print("test finish")
        content = "Test over!!!!!!!!"
        feishu.send_text(content)
        break
ssh.close_connect()
