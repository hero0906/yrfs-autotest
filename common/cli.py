#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
from config import consts
import traceback

logger = logging.getLogger(__name__)


class YrfsCli:
    qos_quota_cmd = ""
    version = consts.YRFS_VERSION

    if version == "650":
        yrfscli = {
            # node status check
            'osd_map': 'yrcli --group --type=oss',
            'oss_map': 'yrcli --osd',
            'mds_map': 'yrcli --osd --type=mds',
            'mds_node': 'yrcli --node --type=mds',
            'oss_node': 'yrcli --node --type=oss',
            'group_list': 'yrcli --group --type={}',

            # osd balance
            'osd_snap': 'yrcli --group --type=oss --snapshot',
            'create_osd_snap': 'yrcli --createsnapshot',
            'osd_snap_recover': 'yrcli --osdbalance',

            # client acl
            'acl_ip_add': 'yrcli --acl --op=add --path=/{} --ip={} --mode={}',
            'acl_id_add': 'yrcli --acl --op=add --path=/{} --id={} --mode={}',
            'acl_ip_del': 'yrcli --acl --op=del --path=/{} --ip={}',
            'acl_id_del': 'yrcli --acl --op=del --path=/{} --id={}',
            'acl_list': 'yrcli --acl --op=list',

            # client cli acl control
            'cliacl_list': 'yrcli --cliacl --op=list',
            'cliacl_add': 'yrcli --cliacl --op=add --ip={}',
            'cliacl_del': 'yrcli --cliacl --op=del --ip={}',
            # entry 信息获取
            'get_root_entry': 'yrcli --getentry / --unmounted',
            'get_entry': 'yrcli --getentry /{} --unmounted',
            'get_file_entry': 'yrcli --getentry /{}',
            # 文件创建命令
            'create_file': 'yrcli --create --stripesize={} --stripecount={} --vol=default --unmounted /{} --schema={}',
            # 获取sla信息
            'get_sla': 'yrcli --getsla',
            # fsck_meta
            'fsck_meta': 'yrcli --fsck /data/mds{0}/replica --thread=4 --cfg=/etc/yrfs/mds{0}.d/yrfs-meta.conf',
            # quota
            'quota_set': 'yrcli --setprojectquota --unmounted --path=/{} --spacelimit={} --inodelimit={}',
            'quota_list': 'yrcli --getprojectquota',
            'quota_single_list': 'yrcli --getprojectquota --path=/{} --unmounted',
            'quota_remove': 'yrcli --rmprojectquota --path=/{} --unmounted',
            'quota_update': 'yrcli --setprojectquota --unmounted --path=/{} --spacelimit={} --inodelimit={} --update',
            # qos
            'qos_total_set': 'yrcli --setqos --path=/{} --tbps={} --tiops={} --mops={} --unmounted',
            'qos_part_set': 'yrcli --setqos --path=/{} --wbps={} --rbps={} --wiops={} --riops={} --mops={} --unmounted',
            'qos_single_set': 'yrcli --setqos --path=/{} --tiops={} --unmounted',
            'qos_list': 'yrcli --getqos',
            'qos_remove': 'yrcli --rmqos --path=/{} --unmounted',
            # create dir
            'mkdir': 'yrcli --mkdir /{} -u',
            # service name
            'oss_service': 'yrfs-storage',
            # s3分层系列参数
            'get_s3_config': 'yrcli --getconfig --key=s3',
            'set_tier_time': 'yrcli --setconfig --key=tiering_time_diff --value={}',
            's3_imexec': 'yrcli --setconfig --key=executeRequestImmediately --value=True',
            'get_s3': 'yrcli --s3',
        }

    else:
        if version == "660":
            qos_quota_cmd = {
                # quota
                'quota_set': 'yrcli --projectquota --op=set --unmounted --path=/{} --spacelimit={} --inodelimit={}',
                'quota_list': 'yrcli --projectquota --op=get',
                'quota_single_list': 'yrcli --projectquota --op=get --path=/{} --unmounted',
                'quota_remove': 'yrcli --projectquota --op=rm --path=/{} --unmounted',
                'quota_update': 'yrcli --projectquota --op=set --unmounted --path=/{} --spacelimit={} --inodelimit={} '
                                '--update',
                # qos
                'qos_total_set': 'yrcli --qos --op=set --path=/{} --tbps={} --tiops={} --mops={} --unmounted',
                'qos_part_set': 'yrcli --qos --op=set --path=/{} --wbps={} --rbps={} --wiops={} --riops={} --mops={} '
                                '--unmounted',
                'qos_single_set': 'yrcli --qos --op=set --path=/{} --tiops={} --unmounted',
                'qos_list': 'yrcli --qos --op=get',
                'qos_remove': 'yrcli --qos --op=rm --path=/{} --unmounted',
                # cliacl del command
                'cliacl_del': 'yrcli --cliacl --op=del --ip={}',
                # acl del command
                'acl_ip_del': 'yrcli --acl --op=del --path=/{} --ip={}',
                'acl_id_del': 'yrcli --acl --op=del --path=/{} --id={}',
            }

        else:
            qos_quota_cmd = {
                # quota
                'quota_set': 'yrcli --projectquota --op=add --unmounted --path=/{} --spacelimit={} --inodelimit={}',
                'quota_list': 'yrcli --projectquota --op=list',
                'quota_list_verbose': 'yrcli --projectquota --path=/{} --op=list --verbose -u',
                'quota_single_list': 'yrcli --projectquota --op=list --path=/{} --unmounted',
                'quota_remove': 'yrcli --projectquota --op=delete --path=/{} --unmounted',
                'quota_update': 'yrcli --projectquota --op=update --unmounted --path=/{} --spacelimit={} '
                                '--inodelimit={}',
                'quota_inode_set': 'yrcli --projectquota --op=add --path=/{} -u --inodelimit={}',
                'quota_inode_update': 'yrcli --projectquota --op=update --path=/{} -u --inodelimit={}',
                'quota_space_set': 'yrcli --projectquota --op=add --path=/{} -u --spacelimit={}',
                'quota_space_update': 'yrcli --projectquota --op=update --path=/{} -u --spacelimit={}',
                # 非空目录quota设置
                "nquota_add": "yrcli --projectquota --op=add --path=/{} -u --spacelimit={} --inodelimit={} --recursive",
                "noquota_add_ignore": "yrcli --projectquota --op=add --path=/{} -u --spacelimit={} --inodelimit={} "
                                      "--recursive --ignoreexisting",
                "quota_continue": "yrcli --projectquota --op=add --path=/{} -u --continue",
                # qos
                'qos_total_set': 'yrcli --qos --op=add --path=/{} --tbps={} --tiops={} --mops={} --unmounted',
                'qos_part_set': 'yrcli --qos --op=add --path=/{} --wbps={} --rbps={} --wiops={} --riops={} --mops={} '
                                '--unmounted',
                'qos_single_set': 'yrcli --qos --op=add --path=/{} --{}={} --unmounted',
                'qos_list': 'yrcli --qos --op=list',
                'qos_remove': 'yrcli --qos --op=delete --path=/{} --unmounted',
                # cliacl del command
                'cliacl_del': 'yrcli --cliacl --op=delete --ip={}',
                # acl del command
                'acl_ip_del': 'yrcli --acl --op=delete --path=/{} --ip={} --force',
                'acl_id_del': 'yrcli --acl --op=delete --path=/{} --id={} --force',
                # 文件创建命令
                'create_file': 'yrcli --create --stripesize={} --stripecount={} --pool=default --unmounted /{} '
                               '--schema={}',
            }

        yrfscli_base = {
            # node status check
            'osd_map': 'yrcli --group --type=oss',
            'oss_map': 'yrcli --osd',
            'mds_map': 'yrcli --osd --type=mds',
            'mds_node': 'yrcli --node --type=mds',
            'oss_node': 'yrcli --node --type=oss',
            'mgr_node': 'yrcli --node --type=mgr',
            'group_list': 'yrcli --group --type={}',
            # osd balance
            'osd_snap': 'yrcli --group --type=oss --snapshot',
            'create_osd_snap': 'yrcli --createsnapshot',
            'osd_snap_recover': 'yrcli --osdbalance',
            # client acl
            'acl_ip_add': 'yrcli --acl --op=add --path=/{} --ip={} --mode={}',
            'acl_id_add': 'yrcli --acl --op=add --path=/{} --id={} --mode={}',

            'acl_list': 'yrcli --acl --op=list',
            # client cli acl control
            'cliacl_list': 'yrcli --cliacl --op=list',
            'cliacl_add': 'yrcli --cliacl --op=add --ip={}',
            # entry 信息获取
            'get_entry': 'yrcli --getentry /{} --unmounted',
            'get_file_entry': 'yrcli --getentry /{}',
            # 获取sla信息
            'get_sla': 'yrcli --getsla',
            # fsck_meta
            'fsck_meta': 'yrcli --fsck /data/mds{0}/replica --thread=4 --cfg=/etc/yrfs/mds{0}.d/yrfs-mds.conf',
            # create dir
            'mkdir': 'yrcli --mkdir /{} -u',
            # service name
            'oss_service': 'yrfs-oss',
            'mds_service': 'yrfs-mds@mds',
            'mgr_service': 'yrfs-mgr',
            # s3分层系列参数
            'get_s3_config': 'yrcli --getconfig --key=s3',
            'set_tier_time': 'yrcli --setconfig --key=tiering_time_diff --value={}',
            's3_imexec': 'yrcli --setconfig --key=executeRequestImmediately --value=True',
            'get_s3': 'yrcli --s3',
            's3_gzip': 'yrcli --setconfig --key=s3_compress_gzip --value={}',
            # s3 tiering
            'bucket_add': 'yrcli --bucket --op=add --hostname={} --protocol={} --bucketname={} '
            '--uri_style={} --region={} --access_key={} --secret_access_key={} --token={} --type={} --bucketid={}',
            "bucket_list": 'yrcli --bucket --op=list',
            "bucket_del": 'yrcli --bucket --op=delete --bucketid={}',
            "tiering_add": "yrcli --tiering --op=add --path=/{} --bucketid={} --coldtime={} --timer={} --id={} -u",
            "tiering_del": "yrcli --tiering --op=delete --id={}",
            "tiering_flush": "yrcli --tiering --op=flush --id={}",
            "tiering_list": "yrcli --tiering --op=list",
            "tiering_mode": "yrcli --tiering --op=setmode --path=/{} --mode={} -u",
            "update_policy": "yrcli --tiering --op=update --id={} --policy={}",
            "mirror_add": "yrcli --tiering --op=add --path=/{} --local={} --public={} --coldtime={} --timer={} --id={} -u",
            "state_update": "yrcli --tiering --op=update --id={} --localstate={}",
            "set_recover": "yrcli --tiering --op=recover --id={}",
            #分层进度recoverstat进度查看
            "s3_recover_stat": "yrcli --tiering --op=recoverstat --id={}",
            # 查看版本信息
            'yrfs_version': 'yrcli --version',
            # mds rebuild:
            "recover_meta": "yrcli --recover --type=mds --groupid={} --restart --fullresync",
            "get_config": "yrcli --getconfig --key={}",
            "set_config": "yrcli --setconfig --key={} --value={}",
        }

        yrfscli = dict(yrfscli_base, **qos_quota_cmd)

    def get_cli(self, command, *args):
        logger.info("Get command: %s, Args: %s" % (command, args))
        try:
            if args:
                argument = self.yrfscli.get(command).format(*args)
            else:
                argument = self.yrfscli.get(command)
            logger.info('Get command: %s success' % argument)
            return argument

        except Exception as e:
            logger.error("Command not found or args fail", traceback.format_exc(e))
