#coding=utf-8

from common.util import sshClient
from config import consts

def verify_mount_point():
    ssh = sshClient(consts.META1)
    stat, res = ssh.ssh_exec('findmnt ' + consts.MOUNT_DIR)
    ssh.close_connect()
    return stat

#mount_point_check = pytest.mark.skipif(verify_mount_point() != 0, reason="server yrfs mount point not exist")