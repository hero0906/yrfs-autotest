# coding=utf-8

import traceback
import re
import logging
from time import sleep
from config.consts import META1, CLIENT, YRFS_VERSION
from common.cli import YrfsCli
from common.util import ssh_exec, sshClient, YamlHandler, ping_test

logger = logging.getLogger(__name__)


# 集群fsck校验
def fsck():
    fsck_cmds = []
    flag = False
    try:
        masterips = getMetaMaster()
        yrfscli = YrfsCli()
        # 获取校验命令
        fsck_cmd = yrfscli.get_cli("fsck_meta")
        # fsck_cmd = yrfscli.get_cli("fsck_meta", "0") + "|tail -n 5"

        str_res = []
        for hostip in masterips:
            ssh = sshClient(hostip)
            # 第一个节点获取mds个数和fsck命令
            if not flag:
                _, mds_num = ssh.ssh_exec("ps axu|grep yrfs-mds|grep -v grep|wc -l")
                for n in range(int(mds_num)):
                    fsck_cmds.append(fsck_cmd.format(n) + "|tail -n 5")
                flag = True
            for cmd in fsck_cmds:
                _, result = ssh.ssh_exec(cmd)
                tailline = result.split("\n")[-1]
                str_res.append(tailline)
            ssh.close_connect()

        if "error" not in "".join(str_res):
            logger.info("cluster %s fsck success." % masterips)
            return 0
        else:
            logger.error("cluster %s fsck failed." % masterips)
            return 1

    except Exception as e:
        logger.error(traceback.format_exc(e))
        return 1


# 获取主机名和ipv4地址对应关系的字典
def get_Cluster_Hostip():
    try:
        # 获取主机名
        newCli = YrfsCli()
        cmd = newCli.get_cli("oss_map") + "|grep -v group|awk '{print $2}'|uniq"
        res = ssh_exec(META1, cmd)
        # hosts_tmp = re.findall(r"(node.+?)<",res)
        # hosts = list(set(hosts_tmp))
        hosts = res.split("\n")
        # hosts.sort(key=hosts_tmp.index)
        logger.info("cluster hostname info: %s." % hosts)

        # 获取ipv4地址信息
        cmd = newCli.get_cli("oss_node")
        res = ssh_exec(META1, cmd)
        ips_raw = re.findall(r"yrfs-oss(.*?)<sync pools>:", res.replace("\n", ""))

        new_ips = []
        for ip_raw in ips_raw:
            ip_tmp = re.findall(r"<(.+?) TCP/IPv4", ip_raw)
            new_ips.append(ip_tmp)

        # ips_tmp = re.findall(r"<(.+?) TCP/IPv4", res)
        # if ips_tmp:
        #     ips = list(set(ips_tmp))
        #     ips.sort(key=ips_tmp.index)
        #     logger.info("cluster ip info: %s." % ips)
        # else:
        #     logger.error("cluster ip info get failed.")
        #
        # slice_num = int(len(ips) / len(hosts))

        # for i in range(len(ips)):
        #     i = i + 1
        #     if i % slice_num == 0:
        #         newip = ips[i - slice_num:i]
        #         newIps.append(newip)
        host_and_ip = dict(zip(hosts, new_ips))
        logger.info("cluster host and ip dict: %s" % host_and_ip)
        return host_and_ip
        # explame
        # {'node1-stor': ['19.16.100.2', '192.168.12.161'], 'node2-stor': ['19.16.100.3', '192.168.12.162'],
        # 'node3-stor': ['19.16.100.4', '192.168.12.163'], 'node4-stor': ['19.16.100.5', '192.168.12.164']}
    except Exception as e:
        logger.error("get cluster hostname and ip failed. %s " % traceback.format_exc(e))


def get_netcard_info():
    # 获取集群的网卡和ip信息
    try:
        # 获取主机名
        newCli = YrfsCli()
        cmd = newCli.get_cli("oss_map") + "|grep -v group|awk '{print $2}'|uniq"
        res = ssh_exec(META1, cmd)
        # hosts_tmp = re.findall(r"(node.+?)<",res)
        # hosts = list(set(hosts_tmp))
        hosts = res.split("\n")
        # hosts.sort(key=hosts_tmp.index)
        logger.info("cluster hostname info: %s." % hosts)
        # 获取ipv4地址信息
        cmd = newCli.get_cli("oss_node")
        res = ssh_exec(META1, cmd)
        ips_tmp = re.findall(r"\n {2}(.+?)<(.+?) TCP/IPv4", res)
        ips = list(set(ips_tmp))
        ips.sort(key=ips_tmp.index)
        logger.info("cluster ip info: %s." % ips)

        slice_num = int(len(ips) / len(hosts))

        newIps = []
        for i in range(len(ips)):
            i = i + 1
            if i % slice_num == 0:
                newip = ips[i - slice_num:i]
                newIps.append(newip)

        host_and_ip = dict(zip(hosts, newIps))
        logger.info("hostname and ip and netcard dict: %s" % host_and_ip)
        return host_and_ip
        # explame
        # {'node1-stor': [(' ens192', '19.16.100.2'), (' ens224', '192.168.12.161')],
        # 'node2-stor': [(' ens192', '19.16.100.3'), (' ens224', '192.168.12.162')],
        # 'node3-stor': [(' ens192', '19.16.100.4'), (' ens224', '192.168.12.163')],
        # 'node4-stor': [(' ens192', '19.16.100.5'), (' ens224', '192.168.12.164')]}
    except Exception as e:
        logger.error("get cluster hostname and ip failed. %s " % traceback.format_exc(e))


def get0ssMaster():
    # 获取两个oss主管理网ip地址
    sshserver = ""
    try:
        newCli = YrfsCli()
        sshserver = sshClient(META1)
        _, ossmaster = sshserver.ssh_exec(newCli.get_cli("oss_map") + "|grep master|awk '{print $2}'|uniq")
        logger.info("cluster oss master node name: %s" % ossmaster)
        oss_masters = ossmaster.split("\n")
        host_ips = get_Cluster_Hostip()
        # 所有的主机名
        hostname = list(host_ips.keys())
        # 验证oss master的ip是不是和1、3节点重合，否则的就是和2、4节点重合
        if oss_masters == hostname[0::2]:
            choice_oss_master = hostname[0::2]
        else:
            choice_oss_master = hostname[1::2]
        logger.info("choice oss master node name: %s" % choice_oss_master)
        # 获取选中的oss master主机名后，在获取管理网ip地址
        oss_master_ips = []
        for ip in choice_oss_master:
            oss_master_ips.append(host_ips[ip][1])
        logger.info("get oss master node manage ip: %s" % oss_master_ips)

        return oss_master_ips
    finally:
        sshserver.close_connect()


def getMetaMaster():
    # 获取meta主业务网ip地址
    try:
        newCli = YrfsCli()
        cmd = newCli.get_cli("mds_map")
        metainfo = ssh_exec(META1, cmd).split("\n")
        logger.info("get mds node info %s" % metainfo)
        # metalines = len(metainfo)
        masterList = []
        for i in metainfo[1:]:
            if i.split()[4] == "master":
                masterList.append(i.split()[1])
        masterList = list(set(masterList))
        metaIps = []
        # choiceMetaName = random.choice(masterList)
        host_and_ip = get_Cluster_Hostip()
        # 这是是假设有两个网卡，第二个ip地址meta节点业务ip，有可能会失败
        for metahost in masterList:
            metaIp = host_and_ip[metahost][1]
            metaIps.append(metaIp)
        logger.info("cluster meta master host ip %s" % metaIps)
        return metaIps

    except Exception as e:
        logger.error(traceback.format_exc(e))


def get_client_storageip(ip):
    """
    通过客户端业务ip，获取到客户端的存储段ip，这里假设客户端跟节点的子网掩至少是两个/16,如果存在多个次网段ip的话，可能会获取失败
    :param ip:
    :return:
    """
    host_and_ip = get_Cluster_Hostip()
    # 获取第字典的第一位值
    storage_ip = [i for i in host_and_ip.values()][0][0]

    prefix_list = storage_ip.split(".")[0:2]
    prefix_str = ".".join(prefix_list)

    client_storage_ip = ssh_exec(ip, "ifconfig|grep -w %s|awk '{print $2}'" % prefix_str)
    logger.info("client %s storage network segment ip: %s." % (ip, client_storage_ip))

    return client_storage_ip


def get_osd_master(filename):
    # 获取文件的主osd节点的ipv4业务网ip地址
    serverip = META1
    sshserver = sshClient(serverip)
    yrcli = YrfsCli()
    try:
        # 获取entry信息
        _, entry_info = sshserver.ssh_exec(yrcli.get_cli("get_entry", filename))
        oss_mirror_group_tmp = re.findall(r'Placement: .*?(\d*), (\d*)', entry_info)
        oss_mirror_group = oss_mirror_group_tmp[0]
        # 定义列表存储oss master 主机名
        node_name = []
        # 查看当前的oss map并过滤查询文件的master oss
        _, oss_map = sshserver.ssh_exec(yrcli.get_cli("oss_map"))
        for m in oss_map.split("\n"):
            m = m.split()
            if m[3] in oss_mirror_group and m[4] == "master":
                node_name.append(m[1])

        node_names = list(set(node_name))
        host_and_ip = get_Cluster_Hostip()
        # 定义存储osd master ip的列表
        osd_masterips = []

        for node_name in node_names:
            osd_ip = host_and_ip[node_name][1]
            osd_masterips.append(osd_ip)

        logger.info("file %s, master osd ip %s." % (filename, osd_masterips))
        return osd_masterips
    except Exception as e:
        logger.error(traceback.format_exc(e))
    finally:
        sshserver.close_connect()


def get_mds_master(filename):
    serverip = META1
    sshserver = sshClient(serverip)
    yrcli = YrfsCli()
    try:
        host_and_ip = get_Cluster_Hostip()
        _, entry_info = sshserver.ssh_exec(yrcli.get_cli("get_entry", filename))
        groupid = re.findall(r"GroupID: (\d.*),", entry_info)
        groupid = "".join(groupid)
        # 提取[]里面的内容，但不包括方括号。
        cmd = yrcli.get_cli("mds_map") + "|awk '{if ($4==%s&&$5==\"master\")print $2}'" % "".join(groupid)
        _, meta_hostname = sshserver.ssh_exec(cmd)

        meta_ip = host_and_ip[meta_hostname][1]

        logger.info("file %s, master mds ip %s and groupid %s." % (filename, meta_ip, groupid))
        # 返回groupid 和 meta master节点
        return groupid, meta_ip
    except Exception as e:
        logger.error(traceback.format_exc(e))
    finally:
        sshserver.close_connect()


def get_entry_info(filename):
    """
    返回entry信息所有项目的字典
    区分664以前的版本664版本和670版本
    :param filename: file path
    :return: dict
    {'EID': '0006561A4B2A7', 'PID': 'yrcf', 'Meta Redundancy': 'Mirror', 'GroupID': '1',
    'nodename': 'node1-stor', 'nodeid': '101', 'TieringID': '1', 'ProjectID': '0',
    'S3Mode': 's3seek', 'Data Redundancy': 'Mirror', 'Stripe Size': '1M', 'Stripe Count': '2',
    'Inode hash path': '53/2A/0006561A4B2A7'}
    """
    serverip = META1
    ssh = sshClient(serverip)
    get_entry = "yrcli --getentry {} -u -v"
    yrfs_version = int(YRFS_VERSION)
    # 获取文件的entry信息,并将各项值转换为字典
    stat, res = ssh.ssh_exec(get_entry.format(filename))
    ssh.close_connect()
    entry_info = {}
    entry_list = []
    if stat == 0:
        for i in res.split("\n"):
            if ":" in i:
                if "," in i:
                    i = i.split(", ")
                    entry_list = entry_list + i
                else:
                    entry_list.append(i)
        entry_list = [i.split(": ") for i in entry_list]
        for n in entry_list:
            if "NodeID" in n:
                node_id = n[1]
                # 判断是664以前的版本还是664以后的版本
                if yrfs_version < 664:
                    nodeid_tmp = re.findall("(.*)<(.*)>", node_id)
                    nodename = nodeid_tmp[0][0]
                    nodeid = nodeid_tmp[0][1]
                elif 670 > yrfs_version >= 664:
                    nodeid_tmp = re.findall(r".*[.](.*)_(.*)", node_id)
                    nodeid = nodeid_tmp[0][1]
                    nodename = nodeid_tmp[0][0]
                elif yrfs_version >= 670:
                    nodeid_tmp = re.findall(r".*[.](.*)[.](.*)", node_id)
                    nodeid = nodeid_tmp[0][1]
                    nodename = nodeid_tmp[0][0]
                entry_info["nodename"] = nodename
                entry_info["nodeid"] = nodeid
            elif "Stripe Count" in n:
                count = n[1]
                count = re.findall(r"([\d.*])", count)
                entry_info[n[0]] = count[0]
            else:
                entry_info[n[0]] = n[1]
        logger.info("Get file: %s entry info %s" % (filename, entry_info))
        return entry_info
    else:
        logger.error("Get file: %s entry info failed." % filename)


def get_mgmt_ips():
    serverip = META1
    sshserver = sshClient(serverip)
    yrcli = YrfsCli()
    mgr_ips = []
    try:
        # mgr存储网络和节点类型
        mgr_hosts_list = []
        _, mgr_hosts = sshserver.ssh_exec(yrcli.get_cli("mgr_node") + "|grep -v \"<\"")
        mgr_hosts = mgr_hosts.split("\n")
        for line in mgr_hosts:
            mgr_hosts_list.append(line.split())
        logger.info("cluster mgmt nodes: %s." % mgr_hosts_list)
        # 获取管理网络和节点类型
        cluster_hosts = get_Cluster_Hostip()
        for n in cluster_hosts.values():
            for m in mgr_hosts_list:
                if m[0] in n:
                    if m[1] == "master":
                        mgr_ips.insert(0, n[1])
                    else:
                        mgr_ips.append(n[1])

        logger.info("get mgmt nodes managemant ip and role %s." % mgr_ips)
        # 结果是mgmt列表嵌套的role和业务ip,master排在第一位
        return mgr_ips

    finally:
        sshserver.close_connect()


def check_cluster_health(check_times=1800, hostip=None):
    """
    查询集群的当前的健康状态。oss 和 mds是否存在非up/clean.
    """
    sshserver = ""
    sleep_time = 10
    logger.info("check cluster health status running.")
    try:
        # 先检查机器是不是在线
        host_and_ip = get_Cluster_Hostip()
        server_ips = [i[-1] for i in host_and_ip.values()]
        for ip in server_ips:
            for i in range(check_times):
                stat = ping_test(ip)
                if stat:
                    break
                else:
                    sleep(sleep_time)
                    continue
            else:
                logger.error("Host %s check online timeout" % ip)
                raise AssertionError("Host not connect")
        if not hostip:
            serverip = META1
        yrcli = YrfsCli()
        mgr_service_part = yrcli.get_cli("mgr_service")
        mgr_service_stat = "systemctl status " + mgr_service_part
        mgr_service_start = "systemctl start " + mgr_service_part
        # 查询oss mds不健康状态命令
        oss_map_check = yrcli.get_cli("oss_map") + "|awk 'NR>1'|grep -v up/clean"
        mds_map_check = yrcli.get_cli("mds_map") + "|awk 'NR>1'|grep -v up/clean"
        # ping 通之后可能服务还没起来
        sleep(10)
        mgr_ips = get_mgmt_ips()
        sshserver = sshClient(serverip)
        # 记录mgr服务状态状态正常就不在检测了。
        mgr_flag = 0
        rebuild_times = 1
        for i in range(check_times):
            sleep(10)
            # 每个节点mgr检测次数记录
            mgr_reboot_times = 1
            if mgr_flag == 0:
                for mgr_ip in mgr_ips:
                    for n in range(check_times):
                        sshmgr = sshClient(mgr_ip)
                        mgr_stat, _ = sshmgr.ssh_exec(mgr_service_stat + " > /dev/null 2>&1")
                        if mgr_stat != 0:
                            logger.warning(
                                "Node %s mgr service was down and trying reboot times: %s" % (mgr_ip, mgr_reboot_times))
                            sshmgr.ssh_exec(mgr_service_start)
                        else:
                            logger.info("Node %s mgr service status health." % mgr_ip)
                            break
                        mgr_reboot_times = mgr_reboot_times + 1
                        logger.info("Sleep 10s.")
                        sleep(sleep_time)
                    else:
                        logger.error("Cluster check health timeout.")
                        raise AssertionError("Cluseter not health")
                else:
                    mgr_flag = 1

            osd_health_stat, osd_res = sshserver.ssh_exec(oss_map_check)
            mds_health_stat, mds_res = sshserver.ssh_exec(mds_map_check)

            if osd_health_stat != 0 and mds_health_stat != 0:
                logger.info("Cluster %s current status health." % serverip)
                return 0
            else:
                logger.info("Sleep 10s.")
                sleep(sleep_time)
                logger.warning("Cluster ill-health, please wait rebuild over, times: "
                               "%s.\nosd status dirty:\n%s,\nmds status dirty:\n%s" % (
                                   str(rebuild_times), osd_res, mds_res))
                rebuild_times = rebuild_times + 1
                continue
        else:
            logger.error("Cluster check health timeout.")
            raise AssertionError("Cluseter not health")
    finally:
        sshserver.close_connect()


def check_version():
    filename = "cluster_version"
    # 获取集群的软件版本
    version_cmd = "yrcli --version"
    serverip = META1
    sshserver = sshClient(serverip)

    try:
        ver_stat, ver_res = sshserver.ssh_exec(version_cmd)
        if ver_stat == 0:
            logger.info("yrfs verison: %s." % ver_res)
            version = ver_res.split(":")[1]
            data = {"version": version}
            yamlhanlder = YamlHandler(filename)
            yamlhanlder.write_yaml(data)
            # yaml_new = YamlHandler("../config/cluster_info.yaml")
            # yaml_new.write_yaml(data)
            return data
        else:
            exit()
            logger.error("The current version is not available.")
    finally:
        sshserver.close_connect()


def cluster_info_collection():
    # 获取集群节点名称与ip的对应关系字典
    filename = "cluster_info"
    logger.info("collcetion cluster info save yaml %s." % filename)
    server_info = get_netcard_info()
    # 获取客户端的存储网络ip
    client_ips = []
    for ip in CLIENT:
        client_ip = get_client_storageip(ip)
        client_ips.append(client_ip)
    clientip = {"clientip": client_ips}
    # 合并上述集群信息
    data = dict(server_info, **clientip)
    yamlhanlder = YamlHandler(filename)
    yamlhanlder.write_yaml(data)
