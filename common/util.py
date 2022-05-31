# coding=utf-8

import paramiko
import os
import traceback
import subprocess
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from configparser import SafeConfigParser
import yaml
# from common.log import log_setup
import logging
from config.consts import TESTDATA_PATH, USERNAME, PASSWORD
from netaddr.ip import IPAddress

logger = logging.getLogger(__name__)


class sshClient:
    def __init__(self, ip, username=USERNAME, password=PASSWORD, port=22, linux=True, timeout=3600):

        self.ip = ip
        self.port = port
        self.linux = linux
        self.password = password
        self.username = username
        self.timeout = timeout

        if not self.linux:
            self.username = "administrator"
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.ip, port=self.port, username=self.username, password=self.password,
                                look_for_keys=False, timeout=self.timeout)
            logger.info("Host %s connected." % self.ip)
        except Exception as e:
            logger.error(traceback.format_exc(e))

    def close_connect(self):
        self.client.close()
        logger.info("Host %s session close." % self.ip)

    def ssh_exec(self, cmd, timeout=3600):

        stdin, stdout, stderr = self.client.exec_command(cmd, timeout)

        if cmd[-1] == "&":
            logger.info("Host: %s, Cmd: %s backgroud." % (self.ip, cmd))

        else:
            logger.info("Host: %s, Cmd: %s." % (self.ip, cmd))
            if self.linux:
                result = stdout.read().decode().rstrip("\n").lstrip("\n")
                err_result = stderr.read().decode().rstrip("\n").lstrip("\n")
            else:
                result = stdout.read().decode("gbk").rstrip("\n").lstrip("\n")
                err_result = stderr.read().decode("gbk").rstrip("\n").lstrip("\n")

            status = stdout.channel.recv_exit_status()
            if status == 0:
                logger.info("Stdout: %s, Sterr: %s, Status: %s." % (result, err_result, status))
            else:
                logger.error("Stdout: %s, Sterr: %s, Status: %s." % (result, err_result, status))
            if result:
                # logger.info("Output: %s, Status: %s." % (result.strip("\n"), status))
                return status, result
            elif err_result:
                # if status == 0:
                #     logger.info("Result: success, output: %s." % (err_result.strip("\n")))
                #     return (status, err_result)
                # else:
                # logger.info("Output: %s, Status: %s." % (err_result.strip("\n"), status))
                return status, err_result
            else:
                # if status == 0:
                #     logger.info("Result: success, output: None")
                #     return (status, None)
                # else:
                #     logger.error("Result: failed, output: None")
                return status, None


def ssh_exec(ip, cmd, username=None, password=None):
    """
    Description : ssh 节点登陆并执行命令
    param: ip,cmd
    return :执行结果
    """
    global ssh
    if password:
        password = password
    else:
        password = PASSWORD

    if username:
        username = username
    else:
        username = "root"
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # result = stdout.readlines().decode()
        result = stdout.read().decode().rstrip("\n")
        # err_result = stderr.readlines().decode()
        err_result = stderr.read().decode().rstrip("\n")
        if result:
            # result = result.decode(encoding='UTF-8',errors='strict')
            logger.info("ip: %s ,command: %s ,success, result:\n%s" % (ip, cmd, result.strip("\n")))
            # return result.decode(encoding='UTF-8')
            return result
        elif err_result:
            logger.info("ip: %s ,command: %s ,success, result:\n%s" % (ip, cmd, err_result.strip("\n")))
            # return err_result.decode(encoding='UTF-8')
            return err_result
        else:
            logger.info("ip: %s ,command: %s ,success" % (ip, cmd))

    except Exception as e:
        logger.error(traceback.format_exc(e))
    finally:
        ssh.close()
        # logger.info("close ssh session")


def read_config(file_name=None):
    """
    读取配置文件信息，返回文件对象
    :param file_name: 配置文件名,不带后缀
    :return: obj
    """
    try:
        config_path = os.path.join(TESTDATA_PATH, "%s.yaml" % file_name)
        with open(config_path, "r") as f:
            p = f.read()
        data = yaml.load(p, Loader=yaml.FullLoader)
        logger.info("read config file %s" % config_path)
        return data
    except Exception as e:
        logger.error(traceback.format_exc(e))


class YamlHandler:
    def __init__(self, filename):
        self.filename = filename
        self.encoding = "utf-8"

    def read_yaml(self):
        try:

            with open(self.filename, encoding=self.encoding) as f:
                logger.info("read yaml file: %s." % self.filename)
                return yaml.load(f.read(), Loader=yaml.FullLoader)

        except Exception as e:
            logger.error(traceback.format_exc(e))

    def write_yaml(self, data):
        try:
            with open(self.filename, encoding=self.encoding, mode='w') as f:
                logger.info("write data: %s, to yaml file: %s." % (data, self.filename))
                return yaml.dump(data, stream=f, allow_unicode=True)
        except Exception as e:
            logger.error(traceback.format_exc(e))

    def update_yaml(self, data):
        try:
            origin_data = self.read_yaml()
            for key in data.keys():
                if key in origin_data:
                    origin_data[key] = data[key]
            self.write_yaml(origin_data)
            logger.info("update data: %s, from yaml file: %s." % (data, self.filename))

        except Exception as e:
            logger.error(traceback.format_exc(e))


def ip6_Prefix(ip6_addr):
    """
    :param ip6_addr:
    :return: ipv6 address prefix
    """
    prefix = []
    if IPAddress(ip6_addr):
        tmp = ip6_addr.split(':')
        for part in tmp[:4]:
            if part:
                prefix.append(part)
            else:
                break
    if len(prefix) < 4:
        ip6_prefix = ":".join(prefix) + "::/64"
    else:
        ip6_prefix = ":".join(prefix) + "/64"

    logger.info('ip6 address: %s prefix: %s' % (ip6_addr, ip6_prefix))

    return ip6_prefix


def ping_test(ip):
    stat, res = subprocess.getstatusoutput("ping -c 1 -w 1 %s" % ip)
    prohib = re.findall(".*Prohibited.*", res)

    if stat == 0:
        logger.info("Host %s reachable." % ip)
        return True
    elif prohib:
        logger.info("Host %s Prohibited." % ip)
        return True
    else:
        logger.error("Host %s unreachable." % ip)
        return False


class sshSftp:

    def __init__(self, ip, username=None, password=None, port=22):

        self.stfp = None
        self.ip = ip
        self.port = port
        if password:
            self.password = password
        else:
            self.password = PASSWORD

        if username:
            self.username = username
        else:
            self.username = USERNAME

        try:
            self.tran = paramiko.Transport(self.ip, self.port)
            self.tran.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.tran)
            logger.info("SFTPClient connect to host: %s, port: %s." % (self.ip, self.port))

        except Exception as e:
            logger.error(traceback.format_exc(e))

    def sftp_mkdir(self, path, mode=777):
        try:
            self.sftp.mkdir(path, mode)
            logger.info("host %s sftp mkdir %s %s." % (self.ip, path, mode))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_rmdir(self, path):
        try:
            self.sftp.rmdir(path)
            logger.info("host %s sftp rmdir %s." % (self.ip, path))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_truncate(self, path, size=10):
        try:
            self.sftp.truncate(path, size)
            logger.info("host %s sftp truncate %s %s." % (self.ip, path, size))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_rename(self, oldpath, newpath):
        try:
            self.sftp.rename(oldpath, newpath)
            logger.info("host %s sftp rename oldpath: %s newpath: %s." % (self.ip, oldpath, newpath))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_createfile(self, filename, modetype="rw", content=None):
        try:
            with self.sftp.open(filename, modetype) as f:
                logger.info("host %s sftp open file %s." % (self.ip, filename))
                if content:
                    f.write(content)
                    logger.info("write filename: %s success." % filename)
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_remove(self, path):
        try:
            self.sftp.remove(path)
            logger.info("host %s sftp remove file path %s." % (self.ip, path))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_upload(self, local_path, remote_path):
        try:
            self.sftp.put(local_path, remote_path)
            logger.info("host %s sftp upload %s to %s." % (self.ip, local_path, remote_path))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def sftp_download(self, remote_path, local_path):
        try:
            self.stfp.get(remote_path, local_path)
            logger.info("host %s sftp download %s to %s." % (self.ip, remote_path, local_path))
            return 0
        except Exception as e:
            logger.error(traceback.format_exc(e))
            return 1

    def close_connect(self):
        self.tran.close()
        logger.info("SFTPClient connect to host: %s, port: %s closed." % (self.ip, self.port))


def send_email(content, contype="html", users="test"):
    msg = MIMEMultipart()
    msg["from"] = "caoyi@yanrongyun.com"

    if users == 'test':
        mail_to = [
            "hanlina@yanrongyun.com",
            "mayunle@yanrongyun.com",
            "zhanghuan@yanrongyun.com",
            "xiangzengbao@yanrongyun.com",
            "niuaijie@yanrongyun.com",
            'caoyi@yanrongyun.com'
        ]
    elif users == 'public':
        mail_to = [
            "wanghaitao@yanrongyun.com",
            "niuaijie@yanrongyun.com",
            "wangpengfei@yanrongyun.com",
            "lijunhong@yanrongyun.com",
            "lixiangping@yanrongyun.com",
            "mayunle@yanrongyun.com",
            "liuhuang@yanrongyun.com",
            "caoyi@yanrongyun.com"
        ]
    else:
        print("参数错误!")
        mail_to = [
            'caoyi@yanrongyun.com',
        ]
    print("users: %s" % mail_to)
    msg['to'] = ','.join(mail_to)
    msg["subject"] = "AutoTestReport " + time.strftime("%m-%d-%H%M%S")

    txt = MIMEText(content, contype, "utf-8")  # 邮件正文
    msg.attach(txt)

    # att = MIMEText(report, "base64", "utf-8")  # 附件
    # att["Content-Type"] = "application/octet-stream"
    # att["Content-Disposition"] = "attachment; filename=" + os.path.basename(file_name)
    # msg.attach(att)
    try:
        smtp_obj = smtplib.SMTP()
        smtp_obj.connect("smtp.mxhichina.com", "25")
        state, _ = smtp_obj.login("caoyi@yanrongyun.com", "Passw0rd@123")
        if state == 235:
            smtp_obj.sendmail(msg["from"], mail_to, msg.as_string())
            print("Sent mail successfully!")
        smtp_obj.quit()
    except smtplib.SMTPException as e:
        print(traceback.format_exc(e))


def create_html(version, passed, failed, percent, report, failed_detail):
    """
    生成html报告
    """
    logger.info("Make html: ", version, passed, failed, percent, report, failed_detail)
    middle = ""
    head = """
        <!DOCTYPE html><html lang="en">
        <body leftmargin="8" marginwidth="0" topmargin="8" marginheight="4" offset="0">
            <table width="95%ds" cellpadding="0" cellspacing="0"  style="font-size: 11pt; font-family: Tahoma, Arial, Helvetica, sans-serif">
                <tr>
                    本邮件由系统自动发出，无需回复！<br/>
                    各位同事，大家好，以下为YRFS自动化测试报告。</br></tr>
                <tr><td><br/><b><font color="#0B610B">自动化测试报告<br></font></b>
                    <hr size="2" width="100%ds" align="center" /></td></tr>
                <tr><td><ul>
                        <li>测试版本 ：{0}</li>
                        <li>成功：<font color="green">{1}</font></li>
                        <li>失败：<font color="red">{2}</font></li>
                        <li>通过率： {3}</li>
                        <li>完整测试报告：<a HREF=>{4}                   </a></li>
                        </ul></tr><tr><td>
                    <b><font color="#0B610B">执行失败用例详情</font></b>
        　　　　    <hr size="2" width="100%" align="center" /></td>
                </tr><tr><td><table border="5">
    """.format(version, passed, failed, percent, report)

    for detail in failed_detail:
        middle = middle + "<tr><td>{}</td></tr>".format(detail)

    tail = "</table></td></tr></table></body></html>"

    html_report = head + middle + tail

    return html_report

