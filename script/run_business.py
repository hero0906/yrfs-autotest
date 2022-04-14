# coding=utf-8
"""
@Desciption : 业务运行
@Time : 2020/09/01 20:26
@Author : caoyi
"""
from time import sleep
import time
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.util import sshSftp, sshClient
from config import consts
from common.log import log_setup
from script.feishu import FeiShutalkChatbot
from depend.client import client_mount

logger = log_setup()

testpath = "/mnt/yrfs/autotest_long_steady"
# webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/bbffe695-40dc-4dc5-87e3-694f1bba172e"
webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/d127b637-cf4e-4c18-99c6-30f1b864979d"
SECRET = "80BlPfDjq92F6GjD1fIR7d"

class RunTestToolS():

    def __init__(self, clientip=None, serverip=None):
        if clientip:
            self.clientip = clientip
        else:
            self.clientip = consts.CLIENT[0]

        if serverip:
            self.serverip = serverip
        else:
            self.serverip = consts.META1

    def run_vdbench(self):
        sshclient = sshClient(self.clientip)
        sshsftp = sshSftp(self.clientip)
        try:
            # 挂载客户端跑业务
            stat = client_mount(self.clientip, acl_add=True)
            assert stat == 0, "client mount failed"
            # 检查客户端java是否安装
            java_stat, _ = sshclient.ssh_exec("java -version")
            if java_stat != 0:
                ins_stat, _ = sshclient.ssh_exec("yum -y install java")
                if ins_stat != 0:
                    logger.error("java not install in this node,test will skip.")
                    raise AssertionError
            # 检查vdbench是否安装
            vd_stat, _ = sshclient.ssh_exec("/opt/vdbench547/vdbench -t")
            if vd_stat != 0:
                logger.info("not found vdbench, wait install.")
                sshsftp.sftp_upload("tools/vdbench547.tar.gz", "/opt/vdbench547.tar.gz")
                sshclient.ssh_exec("tar -zxvf /opt/vdbench547.tar.gz -C /opt")
            # 创建测试目录
            sshclient.ssh_exec("mkdir -p %s" % testpath)
            # 执行测试工具
            vdbench_config = "messagescan=no\n" \
                             "fsd=fsd1,anchor=%s,depth=3,width=5,files=40000,size=4K,shared=yes\n" % testpath + \
                             "fwd=default,xfersize=4K,fileio=random,fileselect=random,rdpct=50,threads=8\n" \
                             "fwd=fwd1,fsd=fsd1\n" \
                             "rd=rd1,fwd=fwd*,fwdrate=max,format=restart,elapsed=4000000,interval=1"

            sshsftp.sftp_createfile("/opt/vdbench547/auotest_long_steady", content=vdbench_config)
            logger.info("vdbench running.")
            vd_log = "/tmp/vdbench-" + time.strftime('%m%d-%H%M%S', time.localtime(time.time()))
            vd_output = "/tmp/autotest_vdbench_output"
            sshclient.ssh_exec(
                "/opt/vdbench547/vdbench -f /opt/vdbench547/auotest_long_steady -vq -o %s > %s 2>&1 &" % (
                    vd_log, vd_output))
            # 检查测试是否存在故障
            while True:
                stat, _ = sshclient.ssh_exec("ps axu|grep auotest_long_steady|grep -v grep")
                if stat == 0:
                    logger.info("vdbench process running, sleep 600s")
                    sleep(600)
                    continue
                else:
                    logger.error("vdbench run failed.")
                    break
            # 发送失败信息
            _, version = sshclient.ssh_exec("yrcli --version")
            _, output = sshclient.ssh_exec("tail -n 20 %s" % vd_output)
            content = "@曹毅 我出问题了！！！\n[vdbench test failed]\ncluster version: %s\n" \
                      "client: %s\nserver: %s\nlog summary: \n%s\nlog path: %s." % \
                      (version, self.clientip, self.serverip, output, vd_log)
            print(content)
            logger.info("send feishu")
            feishu = FeiShutalkChatbot(webhook, secret=SECRET)
            feishu.send_text(content)

        except Exception as e:
            logger.error(traceback.format_exc(e))

        finally:
            sshclient.close_connect()
            sshsftp.close_connect()


if __name__ == "__main__":
    runtools = RunTestToolS()
    runtools.run_vdbench()
    # content = "test"
    # feishu = FeiShutalkChatbot(webhook,secret=SECRET)
    # feishu.send_text(content)
