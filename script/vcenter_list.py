#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
connect center
by cy
"""

import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (
    Cpu, Memory, Disk, Ethernet, Cdrom, Serial, Parallel, Floppy, Boot)
#from com.vmware.vcenter_client import Cluster

session = requests.session()

vc_ip = "192.168.0.10"
vc_user = "administrator@vsphere.local"
vc_passwd = "Passw0rd@123"

session.verify = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

vsphere_client = create_vsphere_client(server=vc_ip, username=vc_user, password=vc_passwd, session=session)
print(dir(vsphere_client.vcenter.vm.guest.Identity))
datacenter_list = vsphere_client.vcenter.Datacenter.list()
print("datacenter list:\t", datacenter_list)
cluster_list = vsphere_client.vcenter.Cluster.list()
print("cluster_list|\t",  cluster_list)

folder_list = vsphere_client.vcenter.Folder.list()
for folder_list in folder_list:
    print(folder_list)
storage_list = vsphere_client.vcenter.Datastore.list()
for storage_list in storage_list:
    print(storage_list)
net_list = vsphere_client.vcenter.Network.list()
for net_list in net_list:
    print(net_list)
pool_list = vsphere_client.vcenter.ResourcePool.list()
print(pool_list)
#vm_list = vsphere_client.vcenter.VM.list()
#print(vm_list)

def create():
    GiB = 1024 * 1024 * 1024
    GiBMemory = 1024

    vm_create_spec = VM.CreateSpec(
        guest_os=guest_os,
        name=self.vm_name,
        placement=self.placement_spec,
        hardware_version=Hardware.Version.VMX_11,
        cpu=Cpu.UpdateSpec(count=2,
                           cores_per_socket=1,
                           hot_add_enabled=False,
                           hot_remove_enabled=False),
        memory=Memory.UpdateSpec(size_mib=2 * GiBMemory,
                                 hot_add_enabled=False),
        disks=[
            Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                            scsi=ScsiAddressSpec(bus=0, unit=0),
                            new_vmdk=Disk.VmdkCreateSpec(name='boot',
                                                         capacity=40 * GiB)),
            Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name='data1',
                                                         capacity=10 * GiB)),
            Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name='data2',
                                                         capacity=10 * GiB))
        ],
        nics=[
            Ethernet.CreateSpec(
                start_connected=True,
                mac_type=Ethernet.MacAddressType.MANUAL,
                mac_address='11:23:58:13:21:34',
                backing=Ethernet.BackingSpec(
                    type=Ethernet.BackingType.STANDARD_PORTGROUP,
                    network=self.standard_network)),
            Ethernet.CreateSpec(
                start_connected=True,
                mac_type=Ethernet.MacAddressType.GENERATED,
                backing=Ethernet.BackingSpec(
                    type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
                    network=self.distributed_network)),
        ],
        cdroms=[
            Cdrom.CreateSpec(
                start_connected=True,
                backing=Cdrom.BackingSpec(type=Cdrom.BackingType.ISO_FILE,
                                          iso_file=iso_datastore_path)
            )
        ],
        serial_ports=[
            Serial.CreateSpec(
                start_connected=False,
                backing=Serial.BackingSpec(
                    type=Serial.BackingType.NETWORK_SERVER,
                    network_location=serial_port_network_location)
            )
        ],
        parallel_ports=[
            Parallel.CreateSpec(
                start_connected=False,
                backing=Parallel.BackingSpec(
                    type=Parallel.BackingType.HOST_DEVICE)
            )
        ],
        floppies=[
            Floppy.CreateSpec(
                backing=Floppy.BackingSpec(
                    type=Floppy.BackingType.CLIENT_DEVICE)
            )
        ],
        boot=Boot.CreateSpec(type=Boot.Type.BIOS,
                             delay=0,
                             enter_setup_mode=False
                             ),
        # TODO Should DISK be put before CDROM and ETHERNET?  Does the BIOS
        # automatically try the next device if the DISK is empty?
        boot_devices=[
            BootDevice.EntryCreateSpec(BootDevice.Type.CDROM),
            BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
            BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET)
        ]
    )

    print(
        '# Example: create_exhaustive_vm: Creating a VM using spec\n-----')
    print(vm_create_spec)
    print('-----')
    vm = vsphere_client.vcenter.VM.create(vm_create_spec)
    vm_info = vsphere_client.vcenter.VM.get(vm)
    print(vm_info)
