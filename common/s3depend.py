#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import re
import random
from time import sleep
from common.util import sshClient
from common.cli import YrfsCli
from config import consts

logger = logging.getLogger(__name__)


def check_layer(fname, layer, tierid, mode=None):
    """
    :param fname:  file name
    :param layer:  s3 layer
    :param tierid: tiering id
    :param mode:   s3 mode seek or normal
    :return: none
    """
    yrcli = YrfsCli()
    entry_cmd = yrcli.get_cli("get_entry", fname)
    try:
        sshserver = sshClient(consts.META1)
        for i in range(30):
            _, entryinfo = sshserver.ssh_exec(entry_cmd)
            cur_layer = re.findall("Data Location: (.*)\n", entryinfo)
            cur_layer = "".join(cur_layer)
            # layer 和 mode 是固定的只需校验一次即可
            if i == 0:

                logger.info("File: %s Layer: %s Tieringid: %s Mode: %s." % (fname, layer, tierid, mode))

                tieringid = re.findall("TieringID: (.*)\n", entryinfo)
                assert "".join(tieringid) == tierid, "tiering id error"

                if mode:
                    s3mode = re.findall("S3Mode: (.*)\n", entryinfo)
                    assert "".join(s3mode) == mode, "s3mode not %s" % mode

            if cur_layer == layer:
                logger.info("File: %s in Layer %s." % (fname, layer))
                break
            else:
                logger.warning("File: %s not in layer %s, retry times: %s" % (fname, layer, str(i + 1)))
                sleep(10)
                continue
        else:
            logger.error("File: %s not in expect layer %s." % (fname, layer))
            assert cur_layer == layer, "layer check failed."
    finally:
        sshserver.close_connect()


def create_s3_script(fname, workers=1, bytesize=None, blocks=1, mode="read"):
    """
    :param fname: 读取的文件名字
    :param blocks: int 读取多少个bytesize块
    :param workers: int 多个文件并发读取
    :param bytesize: 一次读取字节数
    :return: script: 生成脚本内容
    """
    script = ""
    random_seek = random.randint(1, 1194)
    # 如果未定义读取的size,则采用随你数值
    if bytesize:
        bytesize = bytesize
    else:
        bytesize = random_seek
    # 判断读还是写
    if mode == "read":
        chunk = "fo.read({})".format(bytesize)
        rw = "rb"
    else:
        chunk = "fo.write(b'hello world!!!!')"
        rw = "wb"

    head = "def test_seek(filename):\n" \
           "    fo = open(filename, '{0}')\n".format(rw)
    script = script + head

    line = ""
    # 连续读取的块数量
    for i in range(blocks):
        t = "    fo.seek({0}, 0)\n" \
            "    chunk = {1}\n" \
            "    if not chunk:\n" \
            "        fo.close()\n" \
            "        return 1\n".format(random_seek, chunk)
        line = line + t

    script = script + line

    line = "    else:\n" \
           "        fo.close()\n" \
           "        return 0\n"
    script = script + line

    if workers == 1:
        line = "res = test_seek('{}')\n" \
               "print(res)\n".format(fname)
        script = script + line
        return script

    else:
        line = "from concurrent.futures import ThreadPoolExecutor\n" \
               "pools = []\n" \
               "pool = ThreadPoolExecutor(max_workers={0})\n" \
               "for i in {1}:\n" \
               "    filename = i\n" \
               "    p = pool.submit(test_seek, filename)\n" \
               "    pools.append(p)\n" \
               "res = 0\n" \
               "for t in pools:\n" \
               "    res = res + t.result()\n" \
               "print(res)".format(workers, fname)
        script = script + line

    return script

def check_recover_stat(tier_id):
    """
    :param tier_id: tiering id
    :return: tiering id recover stat info
    """
    yrcli = YrfsCli()
    recover_cmd = yrcli.get_cli("s3_recover_stat")
    serverip = consts.META1
    recover_dict = {}
    #查看s3 mirror recover stat
    sshserver = sshClient(serverip)
    stat, res = sshserver.ssh_exec(recover_cmd.format(tier_id))
    if stat == 0:
        for line in res.split("\n"):
            line = line.split(": ")
            recover_dict[line[0]] = line[1].strip()
        logger.info("Tiering %s: recover stat info: %s" % (tier_id, recover_dict))
        return recover_dict
    else:
        logger.error("Tiering %s get recvoer info faild." % tier_id)