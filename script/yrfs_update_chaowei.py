# /usr/bin/env python3
# coding=utf-8
import re
import threading
# import argparse
import subprocess
import paramiko
import traceback
import time
from time import ctime
# from queue import Queue
from optparse import OptionParser
# from argparse import ArgumentParser
import sys


# HOST = ["10.16.45.11","10.16.45.12"]

def multi_threads(func, ips):
    threads = []
    for ip in ips:
        tid = threading.Thread(name='func', target=func, args=(ip, cmd))
        threads.append(tid)

    for tid in threads:
        tid.start()
    for tid in threads:
        tid.join()


def exc_cmd(cmd2, ):
    rt = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    rt.wait()
    err = rt.stderr.read().strip()
    out = rt.stdout.read().strip()
    status = rt.returncode

    if status == 0:
        return status, out
    else:
        return status, err


def ssh2(ip, command):
    ssh = ""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, "root", PASSWORD, timeout=60)
        stdin, stdout, stderr = ssh.exec_command(command)

        result = stdout.read().decode().rstrip("\n").lstrip("\n")
        err_result = stderr.read().decode().rstrip("\n").lstrip("\n")
        status = stdout.channel.recv_exit_status()

        if result:
            print(ctime() + '| [%s] connect OK! \033[34m[COMMAND:] %s, [OUTPUT:] %s\033[0m' % (
                ip, command, result.strip("\n")))
            return status, result
        elif err_result:
            print(ctime() + '| [%s] connect OK! \033[35m[COMMAND:] %s, [ERROR OUTPUT:] %s\033[0m' % (
                ip, command, err_result.strip("\n")))
            return status, err_result
        else:
            print(ctime() + '| [%s] connect OK! \033[34m[COMMAND:] %s\033[0m' % (ip, command))
            return status, None

    except Exception as e:
        print(ctime() + '\033[35m%s\t connect Error,\n\033[0m' % ip)
        traceback.print_exc(e)
    finally:
        ssh.close()


def install():
    ipmi_addrs = ["10.16.2.6", "10.16.2.7", "10.16.2.8", "10.16.2.9"]
    ips = ["10.16.2.6", "10.16.2.7", "10.16.2.8", "10.16.2.9"]
    for ipmi_ip in ipmi_addrs:
        exc_cmd("ipmitool -H {0} -U ADMIN -P ADMIN chassis bootdev pxe && ipmitool -H {0} -U ADMIN -P ADMIN power \
              reset".format(ipmi_ip))
    for hostip in ips:
        try:
            status, _ = ssh2(hostip, "uname -a")
        except Exception as e:
            print(ctime() + "connect host ip %s failed." % hostip)
            print(traceback.print_exc(e))


def yrfs_update(config="reboot"):
    repo_bak = ""
    reboot_web = ""
    start = ["systemctl daemon-reload", "systemctl start yrfs-mgmtd", "systemctl start yrfs-storage",
             "systemctl start yrfs-admon", "systemctl start yrfs-client"]
    stop = ["systemctl daemon-reload", "systemctl stop yrfs-client", "systemctl stop yrfs-mgmtd",
            "systemctl stop yrfs-storage", "systemctl stop yrfs-admon"]

    # update_yum = ["yum clean","yum makecache","rpm -qa|grep -E \"yrfs|yanrong\"|xargs yum -y update"]
    update_yum = ["yum clean", "yum makecache", "rpm -qa|grep -E \"yanrong\"|xargs yum -y update"]
    update_client = ["systemctl stop yrfs-client", "yum clean;yum makecache",
                     "rpm -qa|grep -E \"yrfs|yanrong\"|xargs yum -y update", "systemctl daemon-reload",
                     "systemctl start yrfs-client"]

    # "etcdctl del /yrcf/mgmt/datadir/meta.nodes;etcdctl del /yrcf/mgmt/datadir/storage.nodes;etcdctl del " \
    # "/yrcf/mgmt/datadir/client.nodes "

    client_ver = ['grep "yrfs client version" /var/log/messages|tail -n 1']
    storage_ver = ['grep Version /var/log/yrfs-storage.log |tail -n 1']
    meta_ver = ['grep Version /var/log/yrfs-meta@mds*.log|tail -n 1']
    mgmt_ver = ['grep Version /var/log/yrfs-mgmtd.log|tail -n 1']

    reboot_pacemaker = ""

    one_meta_ip = SERVER[0]
    meta_nums_cmd = "ps axu|grep -E \"yrfs-meta|yrfs-mds\"|grep -v grep|wc -l"
    # yrfs_version_cmd = "rpm -qa|grep yrfs|grep -w 6.3"
    yrfs_version_cmd = "yrcli --version"

    _, meta_nums = ssh2(one_meta_ip, meta_nums_cmd)

    version_stat, version_res = ssh2(one_meta_ip, yrfs_version_cmd)
    if version_stat == 0:
        version_res_tmp = re.findall("Version:(.*)", version_res)
        version_res = ''.join(version_res_tmp)[:3]

    else:
        yrfs_version_cmd = "rpm -qa|grep yrfs-utils|head -n 1|awk -F '-' '{print $3}'|awk -F '.' '{print $1$2}'"
        version_stat, version_res = ssh2(one_meta_ip, yrfs_version_cmd)
        assert version_stat == 0, "no yrfs version found."
        version_res = ".".join(version_res)

    meta_service_cmd = ""
    print(version_res)

    if meta_nums == '1':

        if version_res == "6.3":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://10.16.0.22:17285\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-meta.service"
        elif version_res == "6.5":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://10.16.0.22:17283\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-meta.service"
        elif version_res == "6.6"
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://192.168.0.22:17286\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-mds@mds0.service"
        elif version_res == "6.7"
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://192.168.0.22:17284\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-mds@mds0.service"
        else:
            print("no matching version!")

    else:

        if version_res == "6.3":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://10.16.0.22:17285\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-meta@mds0.service yrfs-meta@mds1.service"
        elif version_res == "6.5":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://10.16.0.22:17283\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-meta@mds0.service yrfs-meta@mds1.service"
        elif version_res == "6.6":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://192.168.0.22:17286\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-mds@mds0.service yrfs-mds@mds1.service"
        elif version_res == "6.7":
            repo_bak = ['mkdir -p /etc/yum.repos.d/cy_bak', 'mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/cy_bak',
                        'echo -e "[yrcf-6.4]\nname=yrcf-6.4\nenabled=1\nbaseurl=http://192.168.0.22:17284\ngpgcheck=0" > /etc/yum.repos.d/yrcf.repo']
            meta_service_cmd = "yrfs-mds@mds0.service yrfs-mds@mds1.service"

    if version_res == "6.6" or version_res == "6.7":
        start = ["systemctl start yrfs-mgr", "systemctl start yrfs-oss", "systemctl start "
                                                                         "yrfs-agent", "/etc/init.d/yrfs-client start",
                 "systemctl start ctdb", "systemctl start nfs"]

        stop = ["systemctl stop nfs", "systemctl stop ctdb", "systemctl daemon-reload", "umount -l /mnt/yrfs",
                "/etc/init.d/yrfs-client stop", 
                "systemctl stop yrfs-oss", "systemctl stop yrfs-agent","systemctl stop yrfs-mgr",]

        client_ver = ['grep "yrfs client version" /var/log/messages|tail -n 1']
        storage_ver = ['grep Version /var/log/yrfs-oss.log |tail -n 1']
        meta_ver = ['grep Version /var/log/yrfs-mds@mds*.log|tail -n 1']
        mgmt_ver = ['grep Version /var/log/yrfs-mgr.log|tail -n 1']

    if version_stat == 0:

        meta_start_cmd = "systemctl start " + meta_service_cmd
        meta_stop_cmd = "systemctl stop " + meta_service_cmd

        start.insert(2, meta_start_cmd)
        stop.insert(6, meta_stop_cmd)

        check_update_version = storage_ver + meta_ver + mgmt_ver + client_ver

        reboot_web = ["systemctl restart yrcloudfile-dashboard", "service inert-krypton-host restart",
                      "systemctl restart inert-iron-scheduler", "systemctl restart inert-iron-scheduler-beat",
                      "systemctl restart inert-krypton-api"]

        reboot_pacemaker = "pcs resource restart krypton-api-clone&&pcs resource restart krypton-cluster&&su \
                -s /bin/sh -c \"krypton-dbsync\" krypton"

        server_update_cmd = repo_bak + stop + update_yum + start + check_update_version + reboot_web
        client_update_cmd = repo_bak + update_client + client_ver


    else:

        server_update_cmd = repo_bak + update_yum
        client_update_cmd = repo_bak + update_client
    # 662采用wget rpm包方式安装
    # kill_mnt = ["lsof /mnt/*|awk 'NR>1{print $2}'|xargs -I {} kill -9 {}","umount -l /mnt/*"]
    kill_mnt = ["mount|grep yrfs|awk '{print $3}'|xargs -I {} lsof {}|awk 'NR>1{print $2}'| xargs -I {} kill -9 {}",
                "mount|grep yrfs|awk '{print $3}'|xargs -I {} umount -l {}"]
    time_dir = time.strftime('%m-%d-%H%M%S', time.localtime(time.time()))
    centos_rpm = ["wget -c -r -nd -np -k -L -A rpm http://192.168.0.22:17282/v67x-daily/daily-build/rpms/ -P " \
                  "/autotest_rpm/%s > /dev/null 2>&1" % time_dir, "rpm -Uvh /autotest_rpm/%s/yrfs-*.rpm" % time_dir,
                  "systemctl daemon-reload"]

    ubuntu_rpm = [
        "wget -c -r -nd -np -k -L -A yrfs*deb http://192.168.0.22:17286/v66x-daily/daily-build/clients/ubuntu2004/ -P " \
        "/autotest_rpm/%s > /dev/null 2>&1" % time_dir, "dpkg -i /autotest_rpm/%s/yrfs-*.deb" % time_dir,
        "systemctl daemon-reload"]

    centos_update = centos_rpm + kill_mnt + ["/etc/init.d/yrfs-client stop", "/etc/init.d/yrfs-client start"]
    ubuntu_update = ubuntu_rpm + kill_mnt + ["/etc/init.d/yrfs-client stop", "/etc/init.d/yrfs-client start"]

    client_update_cmd = centos_update, ubuntu_update
    server_update_cmd = stop + repo_bak + update_yum + centos_rpm + start + reboot_web

    if config == "reboot":
        print(ctime() + '\033|reboot service.\n\033[0m')
        reboot_server = stop + start + reboot_web
        reboot_client = ["systemctl daemon-reload", "/etc/init.d/yrfs-client stop", "/etc/init.d/yrfs-client start"]

        return (reboot_server, reboot_client, reboot_pacemaker)

    else:
        print(ctime() + '\033|choice command: update yrfs service.\n\033[0m')
        return (server_update_cmd, client_update_cmd, reboot_pacemaker)


if __name__ == '__main__':

    parser = OptionParser(description="upadate yrfs version", usage="%prog [-t] <server|client|all> -c <command>",
                          version="%prog 1.0")
    parser.add_option('-t', '--type', dest='type', type='string', help="server type to update")
    parser.add_option('-r', '--reboot', action="store_true", dest="reboot", help="reboot service")
    parser.add_option('-c', '--command', dest='command', type='string', help="linux shell command")
    options, args = parser.parse_args(args=sys.argv[1:])
    print(options, args)

    assert options.type, "please enter the server type!!!"
    if options.type not in ('server', 'client', 'all'):
        raise ValueError
    # for cmd in (stop,update,start):

    PASSWORD = "Passw0rd"
    SERVER = ["10.16.2.11", "10.16.2.12", "10.16.2.13", "10.16.2.14"]
    CLIENT = ["10.16.2.18", "10.16.2.17"]

    # SERVER = ["192.168.12.161","192.168.12.162","192.168.12.163","192.168.12.164"]
    # CLIENT = ["192.168.12.109","192.168.12.110"]
    # CLIENT = ["192.168.12.109",]

    if options.command:
        cmd = options.command

        if options.type == "client":
            multi_threads(ssh2, CLIENT)
        if options.type == "server":
            multi_threads(ssh2, SERVER)
        if options.type == "all":
            HOST = SERVER + CLIENT
            multi_threads(ssh2, HOST)

    elif options.reboot:

        reboot_server, reboot_client, reboot_pcs = yrfs_update(config="reboot")

        serverip = SERVER[0]

        if options.type == "client":
            for cmd in reboot_client:
                multi_threads(ssh2, CLIENT)
        if options.type == "server":
            for cmd in reboot_server:
                multi_threads(ssh2, SERVER)
            ssh2(serverip, reboot_pcs)
        if options.type == "all":
            for cmd in reboot_client:
                multi_threads(ssh2, CLIENT)
            for cmd in reboot_server:
                multi_threads(ssh2, SERVER)
    else:

        server_update_cmd, client_update_cmd, reboot_pcs = yrfs_update(config="update")

        serverip = SERVER[0]

        if options.type == "client":
            # 超威不同版本需要单独升级
            # for cmd in client_update_cmd:
            for client in CLIENT:
                stat, _ = ssh2(client, "cat /etc/centos-release")
                if stat == 0:
                    for cmd in client_update_cmd[0]:
                        ssh2(client, cmd)
                else:
                    for cmd in client_update_cmd[1]:
                        ssh2(client, cmd)
                    # multi_threads(ssh2, CLIENT)
        if options.type == "server":
            for cmd in server_update_cmd:
                multi_threads(ssh2, SERVER)
            ssh2(serverip, reboot_pcs)
        if options.type == "all":
            for client in CLIENT:
                stat, _ = ssh2(client, "cat /etc/centos-release")
                if stat == 0:
                    for cmd in client_update_cmd[0]:
                        ssh2(client, cmd)
                else:
                    for cmd in client_update_cmd[1]:
                        ssh2(client, cmd)
            # for cmd in client_update_cmd:
            # multi_threads(ssh2, CLIENT)
            for cmd in server_update_cmd:
                multi_threads(ssh2, SERVER)
            ssh2(serverip, reboot_pcs)
