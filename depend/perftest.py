#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import re
from common.util import sshClient

logger = logging.getLogger(__name__)


def vdbench_test(clientip, testpath, bss=("4K", "1M"),
                 operations=("write", "read"),
                 threads=16, files=100, size="100M", times=300, sync=True,
                 report_path=None):
    """
    客户端vdbench性能测试
    :param report_path:
    :param sync:
    :param operations:
    :param clientip:
    :param testpath:
    :param bss:
    :param threads:
    :param files:
    :param size:
    :param times:
    :return:
    """
    # 检查客户端工具是否安装
    global save_name, ssh
    result = ""
    # 先填充数据再测试
    fill_stat = 1
    # 结果数值保存
    perf_res = {}
    for bs in bss:
        if bs[-1] in ("K", "k"):
            fileio = "random"
        else:
            fileio = "sequential"
        for operation in operations:
            config = ""
            config = config + "messagescan=no\n"
            config = config + "fsd=fsd1,anchor=%s,depth=1,width=1,files=%s,size=%s,shared=yes\n" % (
            testpath, files, size)
            config = config + "fwd=default,operation=%s,xfersize=%s,fileio=%s,fileselect=random,threads=%s,openflags=o_direct\n" \
                     % (operation, bs, fileio, threads)
            config = config + "fwd=fwd1,fsd=fsd1\n"

            ssh = sshClient(clientip)
            # 第一次执行时填充数据先
            if fill_stat == 1:
                fill_stat += 1
                config2 = config + "rd=rd1,fwd=fwd*,fwdrate=max,format=restart,elapsed=2,interval=1\n"
                ssh.ssh_exec("echo \"%s\" > /tmp/autotest_perf_vdbench" % config2)
                logger.info("vdbench test data init.")
                vdstat, vdres = ssh.ssh_exec("/opt/vdbench547/vdbench -f /tmp/autotest_perf_vdbench -o /tmp/vdbench \
                            > /dev/null 2>&1")
                assert vdstat == 0, "vdbench run failed."
            # 清理缓存
            if sync:
                ssh.ssh_exec("sync;echo 3 > /proc/sys/vm/drop_caches")
            config = config + "rd=rd1,fwd=fwd*,fwdrate=max,format=restart,elapsed=%s,interval=10\n" % times
            # 写入配置文件
            logger.info("Vdbench: %s %s %s" % (bs, fileio, operation))
            ssh.ssh_exec("echo \"%s\" > /tmp/autotest_perf_vdbench" % config)
            vdstat, vdres = ssh.ssh_exec("/opt/vdbench547/vdbench -f /tmp/autotest_perf_vdbench -o /tmp/vdbench")
            assert vdstat == 0, "vdbench run failed."
            # 截取测试数值
            avg_res = re.findall("(avg.*)", vdres)
            bw_res = avg_res[-1].split()[1]
            # unit_res = re.findall(r"Interval.* (.*/sec)", vdres)[-1]
            # bw_unit = bw_res + unit_res
            if bw_res:
                logger.info("Perfancem Ops: %s." % bw_res)
            else:
                logger.error("Not found result.")
                assert False, "Not found result"
            # 保存结果到文件中
            save_name = "Vdbench_Ops_%s_%s_%s" % (bs, fileio, operation)
            result = result + save_name + "\t" + bw_res + "\n"
            #测试数值字典
            perf_res[bs + operation] = (float(bw_res))
    if not report_path:
        report_path = "/tmp/" + save_name
    ssh.ssh_exec("echo \"{0}\" > {1}".format(result, report_path))
    logger.info("Result save to %s %s" % (clientip, report_path))
    ssh.close_connect()

    logger.info("Fio result dict: %s" % perf_res)

    return perf_res


def fio_test(clientip, testpath, bss=("4K", "1M"),
             rws=("write", "read"),
             numjobs=16, iodepth=64, files=10, size="1000M",
             times=300, sync=True, report_path=None):
    """
    客户端cache fio测试
    :param clientip:
    :param testpath:
    :param bss:
    :param threads:
    :param files:
    :param size:
    :param times:
    :param sync: 是否执行同步操作
    :param report_path: str 报告路径
    :return:
    """
    global save_name, ssh
    perf_res = {}
    result = ""
    fill_stat = 1
    for bs in bss:
        # #bs为k的用随机写
        # if bs[-1] in ("k","K"):
        #     rws = ("randwrite", "randread")
        # else:
        #     rws = rws
        for rw in rws:
            if bs[-1] in ("k", "K"):
                rw = "rand" + rw
            fio_cmd = "fio -ioengine=libaio -name=autotest -ramp_time=5 -size=%s -runtime=%s -time_based " \
                      "-group_reporting -bs=%s -rw=%s -numjobs=%s -iodepth=%s -direct=1 -directory=%s -nrfiles=%s" \
                      "" % (size, times, bs, rw, numjobs, iodepth, testpath, files)

            fio_pre = "fio -ioengine=libaio -name=autotest -ramp_time=5 -size=%s " \
                      "-group_reporting -bs=%s -rw=%s -numjobs=%s -iodepth=%s -direct=1 -directory=%s -nrfiles=%s" \
                      "" % (size , "1m", "write", numjobs, iodepth, testpath, files)
            ssh = sshClient(clientip)
            # 首次执行先创建文件
            if fill_stat == 1:
                fill_stat += 1
                ssh.ssh_exec(fio_pre)
            # 是否清理缓存
            if sync:
                ssh.ssh_exec("sync;echo 3 > /proc/sys/vm/drop_caches")
            # 执行测试
            fiostat, fiores = ssh.ssh_exec(fio_cmd)
            assert fiostat == 0, "fio run failed."
            # 匹配测试结果
            iops = re.findall(r"IOPS=(.*?),", fiores)
            iops = "".join(iops)
            logger.info("Perfancem %s" % iops)
            # 保存结果到文件中
            save_name = "Fio_Ops_%s_%s_%s" % (bs, rw, numjobs)
            result = result + save_name + "\t" + iops + "\n"
            #iops数值有可能是k为结尾的重新计算下
            if iops[-1] == "k":
                iops = float(iops[:-1]) * 1000
                iops = int(iops)
            perf_res[bs + rw] = iops
    if not report_path:
        report_path = "/tmp/" + save_name

    ssh.ssh_exec("echo \"{0}\" > {1}".format(result, report_path))
    logger.info("Result save to %s %s" % (clientip, report_path))
    ssh.close_connect()

    logger.info("Fio result dict: %s" % perf_res)
    return perf_res
