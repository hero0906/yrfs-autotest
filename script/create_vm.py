#!/usr/bin/env python
"""
* *******************************************************
* Copyright (c) VMware, Inc. 2016-2018. All Rights Reserved.
* SPDX-License-Identifier: MIT
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""

__author__ = 'VMware, Inc.'
__vcenter_version__ = '6.5+'

import os
import sys
# from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec, SataAddressSpec, IdeAddressSpec
from time import sleep
from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (
    Cpu, Memory, Ethernet, Boot)
from com.vmware.vcenter.vm_client import (Hardware, Power)
from com.vmware.vcenter_client import VM
from pyVim.task import WaitForTask
from pyVmomi import vim
# from com.vmware.vcenter_client import VM
from vmware.vapi.vsphere.client import create_vsphere_client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.samples.vsphere.common.ssl_helper import get_unverified_session
# from common.samples.vsphere.common import sample_cli
# from common.samples.vsphere.common import sample_util
# from common.samples.vsphere.common.sample_util import pp
from common.samples.vsphere.vcenter.helper import network_helper
from common.samples.vsphere.vcenter.helper import vm_placement_helper
from common.samples.vsphere.vcenter.helper.vm_helper import get_vm
# from common.samples.vsphere.vcenter.setup import testbed
from common.vsphere_base import service_instance, pchelper, tasks
from config import consts
from common.log import log_setup

logger = log_setup()


class CreateVM():

    def __init__(self, client=None, placement_spec=None):
        self.client = client
        self.placement_spec = placement_spec
        # self.standard_network = standard_network
        # self.distributed_network = distributed_network
        # self.vm_name = vm_name
        self.cleardata = None
        # self.mac_addr = mac_addr

        self.host = consts.vcenter["host"]
        self.user = consts.vcenter["user"]
        self.passwd = consts.vcenter["passwd"]
        self.port = consts.vcenter["port"]
        self.dis_verify = consts.vcenter["disable_ssl_verification"]

        self.datacenter_name = "yanrong"
        self.vm_folder_name = "vm"
        self.datastore_name = "16-ssd"
        self.std_portgroup_name = "Mgt Network"
        self.std_portgroup2_name = "Storage Net"
        self.exsi_name = "192.168.0.16"

        # Execute the sample in standalone mode.
        if not self.client:
            #
            # parser = sample_cli.build_arg_parser()
            # parser.add_argument('-n', '--vm_name',
            #                     action='store',
            #                     help='Name of the testing vm')
            # args = sample_util.process_cli_args(parser.parse_args())
            # if args.vm_name:
            #     self.vm_name = args.vm_name
            # self.cleardata = args.cleardata
            skipverification = self.dis_verify
            session = get_unverified_session() if skipverification else None
            self.client = create_vsphere_client(server=self.host,
                                                username=self.user,
                                                password=self.passwd,
                                                session=session)

            self.connect = service_instance.connect(host=self.host,
                                                    user=self.user,
                                                    password=self.passwd,
                                                    port=self.port,
                                                    disable_ssl_verification=self.dis_verify)

    def create_vm(self, datacenter, vm_folder, portgroup, datastore,
                  exsihost, vm_name, cpunum=8, memsize=16,
                  guest_os="CENTOS_7_64", mac_addr=None):
        # Get a placement spec
        # datacenter_name = testbed.config['VM_DATACENTER_NAME']
        # vm_folder_name = testbed.config['VM_FOLDER2_NAME']
        # datastore_name = testbed.config['VM_DATASTORE_NAME']
        # std_portgroup_name = testbed.config['STDPORTGROUP_NAME']
        # dv_portgroup_name = testbed.config['VDPORTGROUP1_NAME']
        # dv_portgroup_name = "Storage Network"

        if not self.placement_spec:
            self.placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
                self.client,
                datacenter,
                vm_folder,
                datastore,
                exsihost)

        # Get a standard network backing
        nics = []
        # standard_network1 = network_helper.get_standard_network_backing(
        #     self.client,
        #     portgroup[0],
        #     datacenter)
        # if mac_addr:
        #     mactype1 = Ethernet.MacAddressType.MANUAL
        # else:
        #     mactype1 = Ethernet.MacAddressType.GENERATED
        # ethspec1 = Ethernet.CreateSpec(
        #             start_connected=True,
        #             # mac_type=Ethernet.MacAddressType.GENERATED,
        #             mac_type=Ethernet.MacAddressType.MANUAL,
        #             type="VMXNET3",
        #             mac_address=mac_addr,
        #             backing=Ethernet.BackingSpec(
        #             # type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
        #             type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #             network=standard_network))
        # if len(portgroup) >= 2:
        #     standard_network2 = network_helper.get_standard_network_backing(
        #         self.client,
        #         portgroup[1],
        #         datacenter)
        # if len(portgroup) >= 3:
        #     standard_network3 = network_helper.get_standard_network_backing(
        #         self.client,
        #         portgroup[2],
        #         datacenter)
        for num, value in enumerate(portgroup):
            standard_network = network_helper.get_standard_network_backing(
                self.client,
                portgroup[num],
                datacenter)
            if mac_addr and num == 0:
                ethspec = Ethernet.CreateSpec(
                    start_connected=True,
                    # mac_type=Ethernet.MacAddressType.GENERATED,
                    mac_type=Ethernet.MacAddressType.MANUAL,
                    type="VMXNET3",
                    mac_address=mac_addr,
                    backing=Ethernet.BackingSpec(
                        # type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=standard_network))
            else:
                ethspec = Ethernet.CreateSpec(
                    start_connected=True,
                    # mac_type=Ethernet.MacAddressType.GENERATED,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    type="VMXNET3",
                    backing=Ethernet.BackingSpec(
                        # type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=standard_network))
            nics.append(ethspec)

        # iso_datastore_path = testbed.config['ISO_DATASTORE_PATH']
        # 不需要配置串口
        # serial_port_network_location = \
        #    testbed.config['SERIAL_PORT_NETWORK_SERVER_LOCATION']

        # GiB = 1024 * 1024 * 1024
        # GiBMemory = 1024
        # if mac_addr:
        #     nics=[
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             # mac_type=Ethernet.MacAddressType.GENERATED,
        #             mac_type=Ethernet.MacAddressType.MANUAL,
        #             type="VMXNET3",
        #             mac_address=mac_addr,
        #             backing=Ethernet.BackingSpec(
        #                 # type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network)),
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             mac_type=Ethernet.MacAddressType.GENERATED,
        #             type = "VMXNET3",
        #             #mac_address='11:23:58:13:21:34',
        #             backing=Ethernet.BackingSpec(
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network2)),
        #     ]
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             mac_type=Ethernet.MacAddressType.GENERATED,
        #             type="VMXNET3",
        #             # mac_address='11:23:58:13:21:34',
        #             backing=Ethernet.BackingSpec(
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network3)),
        #     ]
        # else:
        #     nics=[
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             mac_type=Ethernet.MacAddressType.GENERATED,
        #             #mac_type=Ethernet.MacAddressType.MANUAL,
        #             type="VMXNET3",
        #             #mac_address=mac_addr,
        #             backing=Ethernet.BackingSpec(
        #                 # type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network)),
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             mac_type=Ethernet.MacAddressType.GENERATED,
        #             type = "VMXNET3",
        #             #mac_address='11:23:58:13:21:34',
        #             backing=Ethernet.BackingSpec(
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network2)),
        #         Ethernet.CreateSpec(
        #             start_connected=True,
        #             mac_type=Ethernet.MacAddressType.GENERATED,
        #             type="VMXNET3",
        #             # mac_address='11:23:58:13:21:34',
        #             backing=Ethernet.BackingSpec(
        #                 type=Ethernet.BackingType.STANDARD_PORTGROUP,
        #                 network=standard_network3)),
        #     ]

        vm_create_spec = VM.CreateSpec(
            guest_os=guest_os,
            name=vm_name,
            placement=self.placement_spec,
            hardware_version=Hardware.Version.VMX_14,
            cpu=Cpu.UpdateSpec(count=cpunum,
                               cores_per_socket=1,
                               hot_add_enabled=False,
                               hot_remove_enabled=False),
            memory=Memory.UpdateSpec(size_mib=memsize * 1024,
                                     hot_add_enabled=False),
            # disks=[
            #     Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
            #                     #thinProvisioned=True,
            #                     scsi=ScsiAddressSpec(bus=0, unit=0),
            #                     new_vmdk=Disk.VmdkCreateSpec(name='boot',
            #                                                  capacity=40 * GiB,)
            #                                                 ),
            #     Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name='data1',
            #                                                 capacity=50 * GiB)),
            #     Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name='data2',
            #                                                 capacity=50 * GiB,
            #                                                 ))
            # ],
            nics=nics,
            boot=Boot.CreateSpec(type=Boot.Type.BIOS,
                                 delay=5,
                                 enter_setup_mode=False
                                 ),
            # TODO Should DISK be put before CDROM and ETHERNET?  Does the BIOS
            # automatically try the next device if the DISK is empty?
            boot_devices=[
                BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
                BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET),
                # BootDevice.EntryCreateSpec(BootDevice.Type.CDROM),
            ]
        )
        # print(pp(vm_create_spec))
        vm = self.client.vcenter.VM.create(vm_create_spec)
        print("Created VM '{}'".format(vm_name))
        # 开机
        # print("Power on VM %s" % vm_name)
        # self.client.vcenter.vm.Power.start(vm)
        # print(dir(self.client.vcenter.vm.guest))
        return vm

    def add_disk(self, vm_name, disk_size, disk_type):
        spec = vim.vm.ConfigSpec()
        unit_number = 0
        controller = None
        # get all disks on a VM, set unit_number to the next available
        vm = None
        if vm_name:
            content = self.connect.RetrieveContent()
            vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)
        if vm:
            for device in vm.config.hardware.device:
                if hasattr(device.backing, 'fileName'):
                    unit_number = int(device.unitNumber) + 1
                    # unit_number 7 reserved for scsi controller
                    if unit_number == 7:
                        unit_number += 1
                    if unit_number >= 16:
                        print("we don't support this many disks")
                        return -1
                if isinstance(device, vim.vm.device.VirtualSCSIController):
                    controller = device
            if controller is None:
                print("Disk SCSI controller not found!")
                return -1
            # add disk here
            dev_changes = []
            new_disk_kb = int(disk_size) * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = \
                vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == 'thin':
                disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = 'persistent'
            disk_spec.device.unitNumber = unit_number
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = controller.key
            dev_changes.append(disk_spec)
            spec.deviceChange = dev_changes
            vm.ReconfigVM_Task(spec=spec)
            print("%sGB disk added to %s" % (disk_size, vm.config.name))
            return 0
        else:
            print("VM not found")

    def del_disk(self, vm_name, disk_number):
        # hdd_prefix_label = u"硬盘 "
        hdd_prefix_label = "Hard disk "
        content = self.connect.RetrieveContent()

        print('Searching for VM {}'.format(vm_name))
        vm_obj = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

        if vm_obj:
            hdd_label = hdd_prefix_label + str(disk_number)
            print("HDD %s will be delete" % hdd_label)
            virtual_hdd_device = None
            for dev in vm_obj.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualDisk) \
                        and dev.deviceInfo.label == hdd_label:
                    virtual_hdd_device = dev
            if not virtual_hdd_device:
                raise RuntimeError('Virtual {} could not '
                                   'be found.'.format(virtual_hdd_device))

            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_hdd_spec.device = virtual_hdd_device

            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [virtual_hdd_spec]
            task = vm_obj.ReconfigVM_Task(spec=spec)
            tasks.wait_for_tasks(self.connect, [task])
            print('VM HDD "{}" successfully deleted.'.format(disk_number))
            return True
        else:
            print('VM not found')

    def set_vm_attr(self, vm_name):
        # 连接vcenter
        # si = service_instance.connect(host=self.host,
        #                               user=self.user,
        #                               password=self.passwd,
        #                               port=self.port,
        #                               disable_ssl_verification=self.dis_verify)

        vm = pchelper.get_obj(self.connect.RetrieveContent(), [vim.VirtualMachine], vm_name)
        if not vm:
            logger.error("Unable to locate VirtualMachine.")
            raise SystemExit("Unable to locate VirtualMachine.")

        spec = vim.vm.ConfigSpec()
        opt = vim.option.OptionValue()
        spec.extraConfig = []
        # 需要添加的options配置：
        options_values = {"disk.EnableUUID": "true", }
        print("set vm %s exta config %s" % (vm_name, options_values))
        for k, v in options_values.items():
            opt.key = k
            opt.value = v
            spec.extraConfig.append(opt)
            opt = vim.option.OptionValue()
        # 查看任务状态：
        task = vm.ReconfigVM_Task(spec)
        tasks.wait_for_tasks(self.connect, [task])

    def get_snapshots_by_name_recursively(self, snapshots, snapname):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snapname:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + self.get_snapshots_by_name_recursively(
                    snapshot.childSnapshotList, snapname)
        return snap_obj

    def list_snapshots_recursively(self, snapshots):
        snapshot_data = []
        for snapshot in snapshots:
            snap_text = "Name: %s; Description: %s; CreateTime: %s; State: %s" % (
                snapshot.name, snapshot.description,
                snapshot.createTime, snapshot.state)
            snapshot_data.append(snap_text)
            snapshot_data = snapshot_data + self.list_snapshots_recursively(
                snapshot.childSnapshotList)
        return snapshot_data

    def get_current_snap_obj(self, snapshots, snapob):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.snapshot == snapob:
                snap_obj.append(snapshot)
            snap_obj = snap_obj + self.get_current_snap_obj(
                snapshot.childSnapshotList, snapob)
        return snap_obj

    def snap_opera(self, vm_name, snapname, operatype):
        print("vm: %s %s snapshot: %s" % (vm_name, operatype, snapname))
        dump_memory = False
        quiesce = False
        description = "Test snapshot"
        vm = pchelper.get_obj(self.connect.RetrieveContent(), [vim.VirtualMachine], vm_name)

        if operatype == "create":
            print("Creating snapshot %s for virtual machine %s" % (
                snapname, vm_name))
            WaitForTask(vm.CreateSnapshot(
                snapname, description, dump_memory, quiesce))

        elif operatype in ['remove', 'revert']:
            snap_obj = self.get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList, snapname)
            if len(snap_obj) == 1:
                snap_obj = snap_obj[0].snapshot
                if operatype == "remove":
                    print("Removing snapshot %s" % snapname)
                    WaitForTask(snap_obj.RemoveSnapshot_Task(True))
                else:
                    print("Reverting to snapshot %s" % snapname)
                    WaitForTask(snap_obj.RevertToSnapshot_Task())
            else:
                print("No snapshots found with name: %s on VM: %s" % (
                    snapname, vm_name))

        elif operatype == "list_all":
            print("Display list of snapshots on virtual machine %s" % vm_name)
            snapshot_paths = self.list_snapshots_recursively(
                vm.snapshot.rootSnapshotList)
            for snapshot in snapshot_paths:
                print(snapshot)

        elif operatype == 'list_current':
            current_snapref = vm.snapshot.currentSnapshot
            current_snap_obj = self.get_current_snap_obj(vm.snapshot.rootSnapshotList, current_snapref)
            current_snapshot = "Name: %s; Description: %s; " \
                               "CreateTime: %s; State: %s" % (
                                   current_snap_obj[0].name,
                                   current_snap_obj[0].description,
                                   current_snap_obj[0].createTime,
                                   current_snap_obj[0].state)
            print("Virtual machine %s current snapshot is:" % vm_name)
            print(current_snapshot)

        elif operatype == 'remove_all':
            print("Removing all snapshots for virtual machine %s" % vm_name)
            WaitForTask(vm.RemoveAllSnapshots())

        else:
            print("Specify operation in "
                  "create/remove/revert/list_all/list_current/remove_all")

    def power_on(self, vm_name):
        vm = get_vm(self.client, vm_name)
        self.client.vcenter.vm.Power.start(vm)
        print("Power on VM %s" % vm_name)

    def power_off(self, vm_name):
        vm = get_vm(self.client, vm_name)
        self.client.vcenter.vm.Power.stop(vm)
        print("Power off VM %s" % vm_name)

    def cleanup(self, vm_name):
        vm = get_vm(self.client, vm_name)
        if vm:
            state = self.client.vcenter.vm.Power.get(vm)
            if state == Power.Info(state=Power.State.POWERED_ON):
                self.client.vcenter.vm.Power.stop(vm)
            elif state == Power.Info(state=Power.State.SUSPENDED):
                self.client.vcenter.vm.Power.start(vm)
                self.client.vcenter.vm.Power.stop(vm)
            print("Deleting VM '{}' ({})".format(vm_name, vm))
            self.client.vcenter.VM.delete(vm)


def main():
    for i in range(6):
        #vm_name = "曹毅_670_单副本HA测试_node" + str(i)
        #vm_name = "曹毅_663现网科大的问题bug6357验证测试_节点_ " + str(i)
        vm_name = "曹毅_670_扩容测试_节点" + str(i)
        #mac_addr = "00:60:67:8d:95:b" + str(i)
        #mac_addr = "00:60:67:8d:95:a" + str(i)
        mac_addr = None
        disk_num = 5
        disk_size = 20
        sys_disk_size = 80
        datas = ["15-env-4.1", "15-env-4.1", "15-env-4.2", "15-env-4.2", "15-env-5.2","15-env-5.2"]
        #datas = ["15-share-1", "15-env-4.1", "15-env-4.2", "15-env-4.2", "15-env-5.2","15-env-5.2"]
        #datas = ["14-SSD","14-SSD","14-SSD","14-SSD",]
        create_exhaustive_vm = CreateVM()
        # 删除同名虚机
        print("--------------------------------------")
        create_exhaustive_vm.cleanup(vm_name)
        print("create vm: %s, mac address: %s" % (vm_name, mac_addr))
        create_exhaustive_vm.create_vm(datacenter="yanrong",
                                       vm_folder="vm",
                                       #portgroup=["Mgt Network","Storage Net"],
                                       portgroup=["Mgt Network", "Storage Network", "Storage Network"],
                                       #portgroup=["VM Network", "Storage Net", "Storage Net"],
                                       # datastore="16-ssd",
                                       # datastore="15-ssd3",
                                       datastore=datas[i],
                                       exsihost="192.168.0.15",
                                       vm_name=vm_name,
                                       mac_addr=mac_addr,
                                       cpunum=8,
                                       memsize=16
                                       )
        # 删除默认磁盘
        create_exhaustive_vm.del_disk(vm_name=vm_name, disk_number=1)
        # 创建三块50G磁盘
        for i in range(disk_num):
            sleep(10)
            if i == 0:
                create_exhaustive_vm.add_disk(vm_name=vm_name,
                                              disk_size=sys_disk_size,
                                              disk_type="thick")
            else:
                sleep(10)
                create_exhaustive_vm.add_disk(vm_name=vm_name,
                                              disk_size=disk_size,
                                              disk_type="thick")
        # 配置属性
        create_exhaustive_vm.set_vm_attr(vm_name)
        # 开机设置
        create_exhaustive_vm.power_on(vm_name)
        sleep(10)


if __name__ == '__main__':
    main()
    # create_vm = CreateVM()
    # for i in range(5):
    #     vm = "曹毅_6632_1月26日_节点" + str(i)
    #     # vm = "曹毅_6632_节点" + str(i)
    #     # create_vm.cleanup(vm)
    #     create_vm.power_on(vm)
    #     # create_vm.power_on(vm)
    # for i in range(4):
    #     vm_name = "曹毅_670_单副本HA测试_node" + str(i)
    #     create_exhaustive_vm = CreateVM()
    #     create_exhaustive_vm.add_disk(vm_name=vm_name,
    #                                   disk_size=20,
    #                                   disk_type="thick")
