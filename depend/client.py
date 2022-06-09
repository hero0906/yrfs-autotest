# coding=utf-8
"""
@Desciption : 客户端配操作配置
@Time : 2020/12/25 11:13
@Author : caoyi
"""
import logging
import time
from config import consts
from common.util import sshClient, ip6_Prefix, sshSftp
from common.cli import YrfsCli

logger = logging.getLogger(__name__)


def client_mount(ip, subdir="", mountpoint=consts.MOUNT_DIR,
                 aclid=None, type='ip4', param=None, mode=None,
                 acl_add=False):
    """
    :param mode:
    :param mountpoint:
    :param ip: ip6或者ip4可选
    :param subdir: 挂载子目录
    :param aclid: 设置id权限
    :param type: ip6或者是ip4挂载方式
    :param param: 客户端其他配置参数
    :param acl_add True自动设置acl权限
    """
    server = consts.META1
    client = ip
    yrcli = YrfsCli()
    CLIENTCONF = consts.CLIENT_CONFIG
    MOUNTCONF = consts.CLIENT_MOUNT_FILE
    NETCONF = consts.CLIENT_NET_FILE
    sshserver = sshClient(server)
    sshclient = sshClient(client)
    try:
        # if subdir[0] != "/":
        #     subdir = "/" + subdir

        logger.info("client: %s sub dir: %s mount type: %s mounting." % (ip, subdir, type))
        # 卸载挂载点
        sshclient.ssh_exec("mount|grep yrfs|awk '{print $3}'|xargs -I {} umount {}")
        # assert stat == 0, "umount failed."
        # stop服务
        sshclient.ssh_exec("/etc/init.d/yrfs-client stop")
        # stat, _ = sshclient.ssh_exec("lsmod|grep yrfs")
        # assert stat != 0, "rmmod yrfs failed."
        # 备份现有的client配置文件
        # logger.info("backup client mount file: %s" % consts.CLIENT_MOUNT_FILE)
        # sshclient.ssh_exec("mv {0} {0}.bak".format(consts.CLIENT_MOUNT_FILE))
        if type == "ip6":

            cmd = yrcli.get_cli('oss_node') + "|grep IPv6 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|" + \
                  "awk -F '<' '{print $2}'|grep fe80|uniq|head -n 3"
            _, mgmt_ip6_tmp = sshserver.ssh_exec(cmd).split("\n")
            mgmt_ip6s = ",".join(mgmt_ip6_tmp)
            # 写入ip6地址到client配置文件
            sshclient.ssh_exec('echo "cluster_addr = %s" > %s' % (mgmt_ip6s, CLIENTCONF))
            if param:
                sshclient.ssh_exec('echo "%s" >> %s' % (param, CLIENTCONF))
            # 获取ip6 address前缀
            prefix = ip6_Prefix(mgmt_ip6_tmp[0])
            # 写入net文件
            sshclient.ssh_exec('echo "%s" > %s' % (prefix, consts.CLIENT_NET_FILE))
            # 写入挂载目录到mounts配置文件
            sshclient.ssh_exec(
                "echo -e \"{mountpoint} {config} {path} {Id}\" > {mount_file}".format(mountpoint=mountpoint,
                                                                                      config=CLIENTCONF, path=subdir,
                                                                                      Id=aclid, mount_file=CLIENTCONF))
            sshclient.ssh_exec("/etc/init.d/yrfs-client start")
            stat, res = sshclient.ssh_exec('findmnt ' + mountpoint)
            if stat == 0:
                logger.info("yrfs client: %s, mount dir: %s, aclid: %s, mount type: %s mount success." \
                            % (ip, subdir, aclid, type))
            else:
                logger.error("yrfs client: %s, mount dir: %s, aclid: %s, mount type: %s mount failed." \
                             % (ip, subdir, aclid, type))
        else:
            try:
                # 是否自动设置acl权限
                if acl_add == True:
                    sshserver.ssh_exec(yrcli.get_cli("acl_ip_add", subdir, "*", "rw"))

                cmd = yrcli.get_cli(
                    'oss_node') + "|grep IPv4 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|" + \
                      "awk -F '<' '{print $2}'|uniq|head -n 3"
                _, mgmt_ip4_tmp = sshserver.ssh_exec(cmd)
                mgmt_ip4 = ",".join(mgmt_ip4_tmp.split('\n'))
                # 写入配置文件yrfs-cient.conf
                sshclient.ssh_exec('echo "cluster_addr = %s" > %s' % (mgmt_ip4, CLIENTCONF))
                if param:
                    sshclient.ssh_exec('echo "%s" >> %s' % (param, CLIENTCONF))
                # 配置net文件
                _, net_config = sshserver.ssh_exec("cat " + NETCONF)
                sshclient.ssh_exec("echo \"%s\" > %s" % (net_config, NETCONF))
                # 配置yrfs-mount.confg配置文件
                if aclid:
                    mount_conf = mountpoint + " " + CLIENTCONF + " " + subdir + " " + aclid
                    if mode:
                        mount_conf = mountpoint + " " + CLIENTCONF + " " + subdir + " " + aclid + " yrfs " + mode
                    # sshclient.ssh_exec("echo -e \"{mountpoint} {config} {path} {Id}\" > {mount_file}".format(mountpoint=mountpoint,
                    #         config=consts.CLIENT_CONFIG, path=subdir, Id=aclid, mount_file=consts.CLIENT_MOUNT_FILE))
                else:
                    mount_conf = mountpoint + " " + CLIENTCONF + " " + subdir
                    if mode:
                        mount_conf = mountpoint + " " + CLIENTCONF + " " + subdir + " none yrfs " + mode
                sshclient.ssh_exec("echo \"%s\" > %s" % (mount_conf, MOUNTCONF))
                # 验证客户端挂载点是否存在
                startstat, _ = sshclient.ssh_exec("/etc/init.d/yrfs-client start")
                # assert stat == 0, "client start failed."
                # 检测模块加载成功
                modstat, _ = sshclient.ssh_exec("lsmod|grep yrfs")
                # assert stat == 0, "lsmod yrfs failed."
                # 检查挂载点mount成功
                findstat, _ = sshclient.ssh_exec('findmnt ' + mountpoint)
                # assert stat == 0,"findmnt failed."
                stat = startstat + modstat + findstat

                if stat == 0:
                    logger.info("yrfs client: %s, mount dir: %s, aclid: %s, mount type: %s mount success." \
                                "" % (ip, subdir, aclid, type))
                else:
                    logger.error("yrfs client: %s, mount dir: %s, aclid: %s, mount type: %s mount failed." \
                                 "" % (ip, subdir, aclid, type))
                # 恢复备份文件
                # sshclient.ssh_exec("mv {0}.bak {0}".format(consts.CLIENT_MOUNT_FILE))
            finally:
                if acl_add == True:
                    sshserver.ssh_exec(yrcli.get_cli("acl_ip_del", subdir, "*"))

        return stat

    finally:
        sshclient.close_connect()
        sshserver.close_connect()


def run_vdbench(testpath):
    """
    :param testpath: 测试目录
    :return: vdbench:运行状态
    """
    clientip = consts.CLIENT[0]
    sshclient = sshClient(clientip)
    sshsftp = sshSftp(clientip)

    try:
        # 检查客户端java是否安装
        java_stat, _ = sshclient.ssh_exec("java -version > /dev/null 2>&1")
        if java_stat != 0:
            ins_stat, _ = sshclient.ssh_exec("yum -y install java > /dev/null 2>&1")
            if ins_stat != 0:
                logger.error("java not install in this node,test will skip.")
                raise AssertionError
        # 检查vdbench是否安装
        vd_stat, _ = sshclient.ssh_exec("/opt/vdbench547/vdbench -t > /dev/null 2>&1")
        if vd_stat != 0:
            logger.info("Not found vdbench, will install.")
            sshsftp.sftp_upload("tools/vdbench547.tar.gz", "/opt/vdbench547.tar.gz")
            sshclient.ssh_exec("tar -zxvf /opt/vdbench547.tar.gz -C /opt > /dev/null 2>&1")
        # 执行测试工具
        vdbench_config = "messagescan=no\n" \
                         "fsd=fsd1,anchor=%s,depth=1,width=8,files=400000,size=4K,shared=yes\n" % testpath + \
                         "fwd=default,xfersize=4K,fileio=random,fileselect=random,rdpct=50,threads=8\n" \
                         "fwd=fwd1,fsd=fsd1\n" \
                         "rd=rd1,fwd=fwd*,fwdrate=10,format=restart,elapsed=4000000,interval=2"

        sshsftp.sftp_createfile("/opt/vdbench547/auotest_long_steady", content=vdbench_config)
        logger.info("Vdbench running.")
        vd_log = "/tmp/vdbench-" + time.strftime('%m%d-%H%M%S', time.localtime(time.time()))
        sshclient.ssh_exec("mkdir -p " + vd_log)
        vd_output = "/tmp/autotest_vdbench_output"
        sshclient.ssh_exec(">" + vd_output)
        sshclient.ssh_exec(
            "/opt/vdbench547/vdbench -f /opt/vdbench547/auotest_long_steady -o %s > %s 2>&1 &" % (
                vd_log, vd_output))
        time.sleep(5)
        stat, _ = sshclient.ssh_exec("ps axu|grep vdbench|grep -v grep > /dev/null 2>&1")
        if stat == 0:
            logger.info("Vdbench running.")
        else:
            logger.error("Vdbench run failed")
            sshclient.ssh_exec("cat " + vd_output)
        return stat
    finally:
        sshclient.close_connect()
        sshsftp.close_connect()


def run_fstest(host, testpath):
    """
        :param host: test host
        :param testpath: test dir
        :return: stat
        """
    sshclient = sshClient(host, timeout=1800)
    #sshsftp = sshSftp(host)
    try:
        fstest_dir = "/opt/pjdfstest-yrfs"
        # 检验prove工具是否安装
        stat, _ = sshclient.ssh_exec("which prove")
        if stat != 0:
            sshclient.ssh_exec("yum -y install perl-Test-Harness")
        stat, _ = sshclient.ssh_exec("which prove")
        if stat != 0:
            logger.error("Not Found prove test skip")
            assert False
        # 验证客户端的fstest安装包是否存在.不存在的话就拷贝
        stat, _ = sshclient.ssh_exec("stat " + fstest_dir)
        if stat != 0:
            sshsftp = sshSftp(host)
            sshsftp.sftp_upload("tools/pjdfstest-yrfs.tar.gz", "/opt/pjdfstest-yrfs.tar.gz")
            sshclient.ssh_exec("tar -zxvf /opt/pjdfstest-yrfs.tar.gz -C /opt")
            sshsftp.close_connect()

        logger.info("Fstest runing.")
        fstest_stat, _ = sshclient.ssh_exec("cd %s&&prove -rQ %s" % (testpath, fstest_dir), timeout=600)
        if fstest_stat != 0:
            logger.error("Fstest run failed.")
            assert fstest_stat == 0, "fstest run failed."

    finally:
        sshclient.close_connect()

def run_lustre(host):
    """
    :param host: 测试节点ip
    :return:
    """
    lustre_dir = "/opt/lustre_tools"
    sshclient = sshClient(host)
    #验证客户端是否存在测试目录
    stat, _ = sshclient.ssh_exec("stat " + lustre_dir)
    if stat != 0:
        sshsftp = sshSftp(host)
        sshsftp.sftp_upload("tools/lustre_tools.tar.gz", "/opt/lustre_tools.tar.gz")
        sshclient.ssh_exec("tar -zxvf /opt/lustre_tools.tar.gz -C /opt >/dev/null 2>&1")
        sshsftp.close_connect()
    logger.info("Lustre test running.")
    stat, _ = sshclient.ssh_exec("cd %s&&sh acceptance-small.sh|grep -v test_1|grep FAIL:" % lustre_dir, timeout=600)
    sshclient.close_connect()
    if stat == 0:
        logger.error("Lustre run failed.")
        assert False

def win_client_mount(clientip, subdir="/", clientid="", mount_drive="Z:",
                     appcache="false", shareac="true", drivercache="false",
                     appname="winyrcf-client",acl_add=False):
    '''
    aclid: 客户端挂载的id
    subdir: 挂载子目录名称
    mountpoint: windows客户端挂载点
    cache_type: windows客户端cache类型
    mount_type: ipv4或者ipv6方式挂载
    :return: 挂载状态，0成功，1失败。
    '''
    CLIENTCFG = r'"C:\Program Files (x86)\WinYRCF\cfg\%s.conf"' % appname
    LAUNCHCTL = r'"C:\Program Files (x86)\WinYRCF\bin\launchctl-x64.exe"'
    yrcli = YrfsCli()
    serverip = consts.META1
    sshserver = sshClient(serverip)
    sshclient = sshClient(clientip, linux=False)
    #验证参数是否正确
    default_value = ("false", "true")
    if appcache not in default_value or shareac not in default_value or drivercache not in default_value:
        logger.error("Parameter error")
        raise ValueError("Value not in ", default_value)
    #添加权限
    if acl_add:
        sshserver.ssh_exec(yrcli.get_cli("acl_ip_add", subdir, "*", "rw"))
    # 获取mgmt ip地址
    cmd = yrcli.get_cli(
        'oss_node') + "|grep IPv4 |grep `cat /etc/yrfs/interfaces|head -n1`|awk '{print $1}'|" + \
          "awk -F '<' '{print $2}'|uniq|head -n 3"
    _, mgmt_ip4_tmp = sshserver.ssh_exec(cmd)
    mgmt_ip4 = ",".join(mgmt_ip4_tmp.split('\n'))

    config = '"mount_drive = %s" ' % mount_drive + \
             '"cluster_addr = %s" ' % mgmt_ip4 + \
             '"sys_mount_path = %s" ' % subdir + \
             '"client_id = %s" ' % clientid + \
             '"conn_client_port_udp = 8004" ' + \
             '"conn_nics_file = ../cfg/interfaces" ' + \
             '"conn_subnet_filter_file = ../cfg/net" ' + \
             '"conn_ip_whitelist_file = ../cfg/ipwhitelist" ' + \
             '"log_std_file = ../log/winyrcf-client.log" ' + \
             '"app_cache_dir_cfg_file = ../cfg/cacheDir" ' + \
             '"driver_thread_count = 16" ' + \
             '"app_cache_enabled_flag = %s" ' % appcache + \
             '"file_data_cache_enabled_flag = %s" ' % appcache + \
             '"use_global_shared_access = %s" ' % shareac + \
             '"driver_cache_enabled_flag = %s" ' % drivercache
    #停止服务
    sshclient.ssh_exec("%s stop %s" % (LAUNCHCTL, appname))
    #配置客户端配置文件如果存在则清空，不存在创建新文件
    sshclient.ssh_exec("type nul>%s" % CLIENTCFG)
    sshclient.ssh_exec("for %%i in (%s) do @echo %%~i >> %s" % (config, CLIENTCFG))
    stat, _ = sshclient.ssh_exec("%s start %s" % (LAUNCHCTL, appname))
    if acl_add:
        sshserver.ssh_exec(yrcli.get_cli("acl_ip_del", subdir, "*"))
    if stat == 0:
        logger.info("Winclient: %s mount success." % clientip)
        return 0
    else:
        logger.error("Winclient: %s mount failed." % clientip)
        return 1

    sshclient.close_connect()
    sshserver.close_connect()