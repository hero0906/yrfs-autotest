# coding=utf-8

import logging
from time import sleep
import random
from common.cli import YrfsCli
from common.cluster import getMetaMaster, check_cluster_health
from common.cluster import get_mgmt_ips
from common.cluster import get_netcard_info
from common.cluster import get0ssMaster
from config import consts
from common.util import sshClient

logger = logging.getLogger(__name__)


class makeFault(YrfsCli):

    def __init__(self):
        # meta服务的故障测试
        self.serverip = consts.META1
        # 故障恢复时间
        self.sleeps = 60

    def kill_meta(self, nodenum=1, check=True):
        """
        多meta主服务故障测试
        """
        check_cluster_health()
        logger.info("kill all meta master test running.")
        # 获取mds的信息
        mds_service = self.get_cli("mds_service")
        mds_service = mds_service + "0"
        kill_cmd = "systemctl status %s|grep PID|awk '{print $3}'|xargs -I {} kill -9 {}" % mds_service
        start_cmd = "systemctl start %s" % mds_service
        mds_masters_ip = getMetaMaster()
        # 检测是多节点故障还是单节点故障。
        if nodenum == 1:
            mds_masters_ip = mds_masters_ip[0]

        for mdsip in mds_masters_ip,:
            sshserver = sshClient(mdsip)
            logger.info("kill node: %s %s service." % (mdsip, mds_service))
            sshserver.ssh_exec(kill_cmd)
            sshserver.close_connect()
        logger.info("sleep %s." % self.sleeps)
        sleep(self.sleeps)
        for mdsip in mds_masters_ip,:
            sshserver = sshClient(mdsip)
            logger.info("start node: %s %s service." % (mdsip, mds_service))
            sshserver.ssh_exec(start_cmd)
            sshserver.close_connect()
        if check:
            check_cluster_health()
        logger.info("kill meta master test finish.")

    def reboot_meta(self, crash_cmd=None, check=True):
        '''
        重启一个meta master节点故障测试
        '''
        check_cluster_health()
        logger.info("reboot one meta master node test running.")
        # 获取mds节点信息
        if not crash_cmd:
            crash_cmd = "echo \"c\" > /proc/sysrq-trigger &"
        mds_master_ips = getMetaMaster()
        if self.serverip in mds_master_ips:
            mds_master_ips.remove(self.serverip)
        mdsip = mds_master_ips[0]
        # 故障操作
        sshserver = sshClient(mdsip)
        logger.info("crash meta master node: %s." % mdsip)
        sshserver.ssh_exec(crash_cmd + " &", timeout=10)
        sshserver.close_connect()
        # 确认环境是否恢复正常
        if check:
            check_cluster_health()
        logger.info("reboot meta master node test finish.")

    def kill_oss(self, nodenum=1, check=True):
        '''
        双oss 服务故障测试
        '''
        # 检查集群健康状况
        check_cluster_health()
        logger.info("kill oss service test running.")
        # 获取oss服务信息
        oss_service = self.get_cli("oss_service")
        kill_cmd = "systemctl status %s|grep PID|awk '{print $3}'|xargs -I {} kill -9 {}" % oss_service
        start_cmd = "systemctl start %s" % oss_service
        # 获取oss master主ip地址。
        oss_master_ips = get0ssMaster()
        # 识别使用单节点还是多节点故障测试
        if nodenum == 1:
            oss_master_ips = oss_master_ips[0]
        logger.info("kill oss node: %s." % oss_master_ips)
        # kill oss服务
        for mdsip in oss_master_ips,:
            sshserver = sshClient(mdsip)
            logger.info("kill node: %s oss service." % mdsip)
            sshserver.ssh_exec(kill_cmd)
            sshserver.close_connect()

        logger.info("sleep %s." % self.sleeps)
        sleep(self.sleeps)

        for mdsip in oss_master_ips,:
            sshserver = sshClient(mdsip)
            logger.info("start node: %s oss service." % mdsip)
            sshserver.ssh_exec(start_cmd)
            sshserver.close_connect()
        # 再次检查集群是否恢复正常
        if check:
            check_cluster_health()
        logger.info("kill oss test finish.")

    def reboot_oss(self, crash_cmd=None, check=True):
        '''
        重启一个oss master节点故障测试
        '''
        check_cluster_health()
        logger.info("reboot one meta master node test running.")
        # 获取oss节点信息
        if not crash_cmd:
            # crash_cmd = "echo \"c\" > /proc/sysrq-trigger &"
            crash_cmd = "reboot"
        oss_master_ips = get0ssMaster()
        if self.serverip in oss_master_ips:
            oss_master_ips.remove(self.serverip)
        ossip = oss_master_ips[0]
        sshserver = sshClient(ossip)
        logger.info("Crash Oss Master Node: %s." % ossip)
        sshserver.ssh_exec(crash_cmd + " &", timeout=10)
        sshserver.close_connect()
        # 确认环境是否恢复正常
        if check:
            check_cluster_health()
        logger.info("Reboot Oss Master Node Test finish.")

    def down_oss_net(self, check=True):
        """
        :param check: 是否检测集群健康状态
        :return:
        """
        check_cluster_health()
        logger.info("down oss master storage network runing")
        # 或者存储网网卡名称和mgr master节点的ip
        stroage_netcard_name = list(get_netcard_info().values())[0][0][0]
        down_cmd = "ifdown " + stroage_netcard_name
        up_cmd = "ifup " + stroage_netcard_name
        oss_master_ips = get0ssMaster()
        ossip = random.choice(oss_master_ips)
        sshserver = sshClient(ossip)
        #down掉存储网卡
        logger.info("down host:%s net card:%s" % (ossip, stroage_netcard_name))
        sshserver.ssh_exec(down_cmd)
        sleep(self.sleeps)
        #恢复故障网卡
        logger.info("up host:%s net card:%s" % (ossip, stroage_netcard_name))
        sshserver.ssh_exec(up_cmd)
        #确认环境已恢复正常
        if check:
            check_cluster_health()
        logger.info("Down oss master netcard test finish.")

    def reboot_mgr(self, crash_cmd=None, check=True, master=True):
        '''
        mgr master node reboot故障测试。
        '''
        # 检查集群是否健康
        check_cluster_health()
        logger.info("crash mgr master node test running.")
        if not crash_cmd:
            crash_cmd = "echo \"c\" > /proc/sysrq-trigger &"
        # 获取mgr master节点信息
        mgr_master_ip = get_mgmt_ips()
        mgr_master_ip.remove(self.serverip)
        # crash节点
        if master:
            choice_mgr_ip = mgr_master_ip[0]
        else:
            choice_mgr_ip = mgr_master_ip[1]
        sshserver = sshClient(choice_mgr_ip)
        logger.info("crash mgr master node: %s." % choice_mgr_ip)
        sshserver.ssh_exec(crash_cmd + " &", timeout=10)
        sshserver.close_connect()
        # 再次检查集群状态
        if check:
            check_cluster_health()
        logger.info("crash mgr master node test finish.")

    def kill_mgr(self, check=True, master=True):
        '''
        kill mgr master service故障测试
        '''
        # 检查集群是否健康
        check_cluster_health()
        logger.info("kill mgr master test running.")
        mgr_service = self.get_cli("mgr_service")
        stop_cmd = "systemctl stop " + mgr_service
        start_cmd = "systemctl start " + mgr_service
        # 获取mgr master节点信息
        if master:
            mgr_master_ip = get_mgmt_ips()[0]
        else:
            mgr_master_ip = get_mgmt_ips()[1]
        # kil master节点服务mgr
        sshserver = sshClient(mgr_master_ip)
        logger.info("kill node: %s mgr master service." % mgr_master_ip)
        sshserver.ssh_exec(stop_cmd)
        logger.info("sleep %s." % self.sleeps)
        sleep(self.sleeps)
        logger.info("start node: %s mgr master service." % mgr_master_ip)
        sshserver.ssh_exec(start_cmd)
        sshserver.close_connect()
        # 再次检查集群状态
        if check:
            check_cluster_health()
        logger.info("kill mgr master node test finish.")

    def down_mgr(self, check=True, master=True):
        '''
        down mgr存储网卡故障测试
        '''
        # 检查集群是否健康
        check_cluster_health()
        logger.info("down mgr master network test running.")
        # 或者存储网网卡名称和mgr master节点的ip
        stroage_netcard_name = list(get_netcard_info().values())[0][0][0]

        down_cmd = "ifdown " + stroage_netcard_name
        up_cmd = "ifup " + stroage_netcard_name

        mgr_master_list = get_mgmt_ips()[0]
        if master:
            mgr_master_ip = mgr_master_list[0]
        else:
            mgr_master_ip = mgr_master_list[1]
        sshserver = sshClient(mgr_master_ip)
        logger.info("down mgr master node: %s network: %s." % (mgr_master_ip, stroage_netcard_name))
        # down掉网卡
        sshserver.ssh_exec(down_cmd)
        logger.info("sleep %s." % self.sleeps)
        sleep(self.sleeps)
        # 重新启动网卡
        logger.info("up mgr master node: %s network: %s." % (mgr_master_ip, stroage_netcard_name))
        sshserver.ssh_exec(up_cmd)
        sshserver.close_connect()
        # 检查集群状态是否正常
        if check:
            check_cluster_health()
        logger.info("Down mgr master network test finish.")
