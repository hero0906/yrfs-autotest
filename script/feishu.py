#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@File   :  feiShuTalk.py
@Time   :  2021/9/11 11:45
@Author  :  CY
@Version  :  V1.0.0
@Desciption:
"""

import base64
import hmac
import json
import os
import re
import sys
import time

import requests
import urllib3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.cluster import check_version
from common.log import log_setup
from config import consts
from common.util import send_email, create_html

urllib3.disable_warnings()

logger = log_setup()

try:
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def is_not_null_and_blank_str(content):
    """
    非空字符串
    :param content: 字符串
    :return: 非空 - True，空 - False
    """
    if content and content.strip():
        return True
    else:
        return False


secret = "iYhgTAgWIED8eYuoOL8JOb"
webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/bbffe695-40dc-4dc5-87e3-694f1bba172e"


class FeiShutalkChatbot(object):
    def __init__(self, webhook, secret=secret, pc_slide=False, fail_notice=False):
        '''
        机器人初始化
        :param webhook: 飞书群自定义机器人webhook地址
        :param secret: 机器人安全设置页面勾选“加签”时需要传入的密钥
        :param pc_slide: 消息链接打开方式，默认False为浏览器打开，设置为True时为PC端侧边栏打开
        :param fail_notice: 消息发送失败提醒，默认为False不提醒，开发者可以根据返回的消息发送结果自行判断和处理
        '''
        super(FeiShutalkChatbot, self).__init__()
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.webhook = webhook
        self.secret = secret
        self.pc_slide = pc_slide
        self.fail_notice = fail_notice

    def send_text(self, msg):
        """
        消息类型为text类型
        :param msg: 消息内容
        :return: 返回消息发送结果
        """
        msg = msg
        data = {"msg_type": "post", "at": {}}
        if is_not_null_and_blank_str(msg):  # 传入msg非空
            data["content"] = {"post": {
                "zh_cn": {
                    "title": "自动化测试报告",
                    "content": [
                        [{"tag": "text",
                          "text": msg},
                         {"tag": "at",
                          "user_id": "ccgf8235"}]
                    ]
                }
            }

            }
        else:
            logger.error("text类型，消息内容不能为空！")
            raise ValueError("text类型，消息内容不能为空！")

        data = dict(data, **self.verify())
        logger.debug('text类型：%s' % data)
        return self.post(data)

    def verify(self):

        timestamp = str(round(time.time()))
        key = f'{timestamp}\n{secret}'
        key_enc = key.encode('utf-8')
        msg = ""
        msg_enc = msg.encode('utf-8')
        hmac_code = hmac.new(key_enc, msg_enc, "sha256").digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        # 返回签名校验换算
        return {"timestamp": timestamp, "sign": sign}

    def post(self, data):
        """
        发送消息（内容UTF-8编码）
        :param data: 消息数据（字典）
        :return: 返回消息发送结果
        """
        try:
            post_data = json.dumps(data)
            response = requests.post(self.webhook, headers=self.headers, data=post_data, verify=False)
        except requests.exceptions.HTTPError as exc:
            logger.error("消息发送失败， HTTP error: %d, reason: %s" % (exc.response.status_code, exc.response.reason))
            raise
        except requests.exceptions.ConnectionError:
            logger.error("消息发送失败，HTTP connection error!")
            raise
        except requests.exceptions.Timeout:
            logger.error("消息发送失败，Timeout error!")
            raise
        except requests.exceptions.RequestException:
            logger.error("消息发送失败, Request Exception!")
            raise
        else:
            try:
                result = response.json()
            except JSONDecodeError:
                logger.error("服务器响应异常，状态码：%s，响应内容：%s" % (response.status_code, response.text))
                return {'errcode': 500, 'errmsg': '服务器响应异常'}
            else:
                logger.debug('发送结果：%s' % result)
                # 消息发送失败提醒（errcode 不为 0，表示消息发送异常），默认不提醒，开发者可以根据返回的消息发送结果自行判断和处理
                if self.fail_notice and result.get('errcode', True):
                    time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                    error_data = {
                        "msgtype": "text",
                        "text": {
                            "content": "[注意-自动通知]飞书机器人消息发送失败，时间：%s，原因：%s，请及时跟进，谢谢!" % (
                                time_now, result['errmsg'] if result.get('errmsg', False) else '未知异常')
                        },
                        "at": {
                            "isAtAll": False
                        }
                    }
                    logger.error("消息发送失败，自动通知：%s" % error_data)
                    requests.post(self.webhook, headers=self.headers, data=json.dumps(error_data))
                return result


def report_extract(mail=True):
    # 查找测试报告的内容
    report = "logs/report.html"
    allurelog = "logs/allure-results"
    with open(report, "r+") as f:
        lines = f.read()

    passed = re.findall(r"class=\"passed\">(.+?) passed", lines)
    failed = re.findall(r"class=\"failed\">(.+?) failed", lines)
    skipped = re.findall(r"class=\"skipped\">(.+?) skipped", lines)
    error = re.findall(r"class=\"error\">(.+?) errors</span>", lines)
    # 获取失败用例
    failed_list = re.findall(r"Failed</td>[\s\S]*?<td[\s\S]*?<td>\n\s*([\S].*)\n", lines, re.M)
    failed_line = ["  " + i + "\n" for i in failed_list]
    failed_line = "".join(failed_line)

    cases_num = re.findall(r"<p>(.+?) tests", lines)
    passed_percent = "%.2f%%" % (int("".join(passed)) / int("".join(cases_num)) * 100)
    newreport = "report-%s.html" % time.strftime('%m%d-%H%M%S', time.localtime(time.time()))
    # 备份测试报告
    os.system("cp %s /var/www/html/%s" % (report, newreport))
    pyreport = "http://10.16.2.18/" + newreport
    # 杀掉之前进程
    os.system("ps axu|grep allure|grep -v grep|awk '{print $2}'|xargs -I {} kill -9 {}")
    os.system("nohup allure -q serve %s -p 9006 &" % allurelog)
    allurereport = "http://10.16.2.18:9006"
    # 获取软件版本
    yrfs_version = check_version()
    yrfs_version = "".join(yrfs_version.values())
    # 推送消息到飞书下
    # webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/bbffe695-40dc-4dc5-87e3-694f1bba172e"
    # content = " 版本：%s\n 测试集群：%s\n 成功：%s\n 失败：%s\n 跳过：%s\n 错误：%s\n" \
    #           " 通过率：%.2f%%\n 完整测试报告：%s" \
    #           % (yrfs_version, consts.META1, passed, failed, skipped, error, passed_percent, pyreport)
    #飞书报告
    content_feishu = " 版本:%s\n 测试集群:%s\n 成功:%s\n 失败:%s\n" \
              " 通过率:%s\n 完整测试报告:%s\n 失败用例:\n%s" \
              % (yrfs_version, consts.META1, passed, failed, passed_percent, pyreport, failed_line)
    #print(content_feishu)
    # 创建html报告
    content_mail = create_html(yrfs_version, passed, failed, passed_percent, allurereport, failed_list)
    #报告发送
    feishu = FeiShutalkChatbot(webhook)
    print("Send feishu report")
    feishu.send_text(content_feishu)
    if mail:
        print("Send mail report")
        if int("".join(failed)) < 100:
            send_email(content_mail, users="public")
        else:
            send_email(content_mail, users="test")

if __name__ == "__main__":
    report_extract(mail=False)
