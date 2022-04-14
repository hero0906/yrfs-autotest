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

from com.vmware.vcenter_client import VM

from common.samples.vsphere.vcenter.helper import datastore_helper
from common.samples.vsphere.vcenter.helper import folder_helper
from common.samples.vsphere.vcenter.helper import resource_pool_helper
from common.samples.vsphere.vcenter.helper import datacenter_helper
from com.vmware.vcenter_client import Host


def get_placement_spec_for_resource_pool(client,
                                         datacenter_name,
                                         vm_folder_name,
                                         datastore_name,
                                         host_name,):
    """
    Returns a VM placement spec for a resourcepool. Ensures that the
    vm folder and datastore are all in the same datacenter which is specified.
    """
    resource_pool = resource_pool_helper.get_resource_pool(client,
                                                           datacenter_name)

    folder = folder_helper.get_folder(client,
                                      datacenter_name,
                                      vm_folder_name)

    datastore = datastore_helper.get_datastore(client,
                                               datacenter_name,
                                               datastore_name)

    host = get_host(client, datacenter_name, host_name)
    # Create the vm placement spec with the datastore, resource pool and vm
    # folder
    print("no resource_pool")
    placement_spec = VM.PlacementSpec(folder=folder,
                                      host=host,
                                      #resource_pool=resource_pool,
                                      datastore=datastore
                                      )

    print("get_placement_spec_for_resource_pool: Result is '{}'".
          format(placement_spec))
    return placement_spec

def get_host(client, datacenter_name, host_name):
    """
    Returns the identifier of a folder
    Note: The method assumes that there is only one folder and datacenter
    with the mentioned names.
    """
    datacenter = datacenter_helper.get_datacenter(client, datacenter_name)
    if not datacenter:
        print("Datacenter '{}' not found".format(datacenter_name))
        return None

    filter_spec = Host.FilterSpec(names=set([host_name]),
                                    datacenters=set([datacenter]))

    host_summaries = client.vcenter.Host.list(filter_spec)
    #print(dir(host_summaries))
    if len(host_summaries) > 0:
        host = host_summaries[0].host
        print("Detected host '{}' as {}".format(host_name, host))
        return host
    else:
        print("host '{}' not found".format(host_name))
        return None
