# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: agent.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='agent.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0b\x61gent.proto\"u\n\x0f\x43lientStatsPara\x12\x11\n\tnode_type\x18\x01 \x01(\r\x12\x19\n\x11hide_internal_ips\x18\x02 \x01(\x08\x12\x19\n\x11return_zero_stats\x18\x03 \x01(\x08\x12\x19\n\x11\x63lient_stats_type\x18\x04 \x01(\r\"@\n\x0e\x43lientStatsRet\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0e\n\x06online\x18\x02 \x01(\x08\x12\x12\n\nopcounters\x18\x03 \x03(\x04\"#\n\x0eGetSlaInfoPara\x12\x11\n\twith_root\x18\x01 \x01(\x08\"B\n\rGetSlaInfoRet\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x10\n\x08\x65ntry_id\x18\x02 \x01(\t\x12\x11\n\tsla_value\x18\x03 \x03(\x04\"(\n\tTimeValue\x12\x0c\n\x04time\x18\x01 \x01(\x04\x12\r\n\x05value\x18\x02 \x01(\x04\"D\n\nServerNode\x12\x11\n\tnode_name\x18\x01 \x01(\t\x12\x13\n\x0bnode_num_id\x18\x02 \x01(\r\x12\x0e\n\x06online\x18\x03 \x01(\x08\"!\n\x0fMdsOverviewPara\x12\x0e\n\x06unused\x18\x01 \x01(\x08\"\xde\x01\n\x0eMdsOverviewRet\x12\x18\n\x10\x64isk_space_total\x18\x01 \x01(\x04\x12\x17\n\x0f\x64isk_space_free\x18\x02 \x01(\x04\x12\x17\n\x0f\x64isk_space_used\x18\x03 \x01(\x04\x12\x18\n\x10inode_space_used\x18\x04 \x01(\x04\x12\x1e\n\tnode_info\x18\x05 \x03(\x0b\x32\x0b.ServerNode\x12!\n\rwork_requests\x18\x06 \x03(\x0b\x32\n.TimeValue\x12#\n\x0fqueued_requests\x18\x07 \x03(\x0b\x32\n.TimeValue\"!\n\x0fOssOverviewPara\x12\x0e\n\x06unused\x18\x01 \x01(\x08\"\xcc\x02\n\x0eOssOverviewRet\x12\x18\n\x10\x64isk_space_total\x18\x01 \x01(\x04\x12\x17\n\x0f\x64isk_space_free\x18\x02 \x01(\x04\x12\x17\n\x0f\x64isk_space_used\x18\x03 \x01(\x04\x12\x15\n\rdisk_read_sum\x18\x04 \x01(\x04\x12\x16\n\x0e\x64isk_write_sum\x18\x05 \x01(\x04\x12\x1e\n\tnode_info\x18\x06 \x03(\x0b\x32\x0b.ServerNode\x12\"\n\x0e\x64isk_perf_read\x18\x07 \x03(\x0b\x32\n.TimeValue\x12*\n\x16\x64isk_perf_average_read\x18\x08 \x03(\x0b\x32\n.TimeValue\x12#\n\x0f\x64isk_perf_write\x18\t \x03(\x0b\x32\n.TimeValue\x12*\n\x16\x64isk_per_average_write\x18\n \x03(\x0b\x32\n.TimeValue\"H\n\x0cNodeListPara\x12\x0e\n\x06\x63lient\x18\x01 \x01(\x08\x12\x19\n\x11hide_internal_ips\x18\x02 \x01(\x08\x12\r\n\x05\x61gent\x18\x03 \x01(\x08\"@\n\x08NodeInfo\x12\x0c\n\x04type\x18\x01 \x01(\r\x12\x13\n\x0bnode_num_id\x18\x02 \x01(\r\x12\x11\n\tnode_name\x18\x03 \x01(\t\",\n\x0bNodeListRet\x12\x1d\n\nnode_lists\x18\x01 \x03(\x0b\x32\t.NodeInfo2\x85\x02\n\x05\x41gent\x12\x34\n\x0b\x43lientStats\x12\x10.ClientStatsPara\x1a\x0f.ClientStatsRet\"\x00\x30\x01\x12\x31\n\nGetSlaInfo\x12\x0f.GetSlaInfoPara\x1a\x0e.GetSlaInfoRet\"\x00\x30\x01\x12\x32\n\x0bMdsOverview\x12\x10.MdsOverviewPara\x1a\x0f.MdsOverviewRet\"\x00\x12\x32\n\x0bOssOverview\x12\x10.OssOverviewPara\x1a\x0f.OssOverviewRet\"\x00\x12+\n\x08NodeList\x12\r.NodeListPara\x1a\x0c.NodeListRet\"\x00\x30\x01\x62\x06proto3'
)




_CLIENTSTATSPARA = _descriptor.Descriptor(
  name='ClientStatsPara',
  full_name='ClientStatsPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='node_type', full_name='ClientStatsPara.node_type', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='hide_internal_ips', full_name='ClientStatsPara.hide_internal_ips', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='return_zero_stats', full_name='ClientStatsPara.return_zero_stats', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='client_stats_type', full_name='ClientStatsPara.client_stats_type', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=15,
  serialized_end=132,
)


_CLIENTSTATSRET = _descriptor.Descriptor(
  name='ClientStatsRet',
  full_name='ClientStatsRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ip', full_name='ClientStatsRet.ip', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='online', full_name='ClientStatsRet.online', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='opcounters', full_name='ClientStatsRet.opcounters', index=2,
      number=3, type=4, cpp_type=4, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=134,
  serialized_end=198,
)


_GETSLAINFOPARA = _descriptor.Descriptor(
  name='GetSlaInfoPara',
  full_name='GetSlaInfoPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='with_root', full_name='GetSlaInfoPara.with_root', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=200,
  serialized_end=235,
)


_GETSLAINFORET = _descriptor.Descriptor(
  name='GetSlaInfoRet',
  full_name='GetSlaInfoRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='GetSlaInfoRet.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='entry_id', full_name='GetSlaInfoRet.entry_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='sla_value', full_name='GetSlaInfoRet.sla_value', index=2,
      number=3, type=4, cpp_type=4, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=237,
  serialized_end=303,
)


_TIMEVALUE = _descriptor.Descriptor(
  name='TimeValue',
  full_name='TimeValue',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='TimeValue.time', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='TimeValue.value', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=305,
  serialized_end=345,
)


_SERVERNODE = _descriptor.Descriptor(
  name='ServerNode',
  full_name='ServerNode',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='node_name', full_name='ServerNode.node_name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_num_id', full_name='ServerNode.node_num_id', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='online', full_name='ServerNode.online', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=347,
  serialized_end=415,
)


_MDSOVERVIEWPARA = _descriptor.Descriptor(
  name='MdsOverviewPara',
  full_name='MdsOverviewPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='unused', full_name='MdsOverviewPara.unused', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=417,
  serialized_end=450,
)


_MDSOVERVIEWRET = _descriptor.Descriptor(
  name='MdsOverviewRet',
  full_name='MdsOverviewRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='disk_space_total', full_name='MdsOverviewRet.disk_space_total', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_space_free', full_name='MdsOverviewRet.disk_space_free', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_space_used', full_name='MdsOverviewRet.disk_space_used', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='inode_space_used', full_name='MdsOverviewRet.inode_space_used', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_info', full_name='MdsOverviewRet.node_info', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='work_requests', full_name='MdsOverviewRet.work_requests', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='queued_requests', full_name='MdsOverviewRet.queued_requests', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=453,
  serialized_end=675,
)


_OSSOVERVIEWPARA = _descriptor.Descriptor(
  name='OssOverviewPara',
  full_name='OssOverviewPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='unused', full_name='OssOverviewPara.unused', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=677,
  serialized_end=710,
)


_OSSOVERVIEWRET = _descriptor.Descriptor(
  name='OssOverviewRet',
  full_name='OssOverviewRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='disk_space_total', full_name='OssOverviewRet.disk_space_total', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_space_free', full_name='OssOverviewRet.disk_space_free', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_space_used', full_name='OssOverviewRet.disk_space_used', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_read_sum', full_name='OssOverviewRet.disk_read_sum', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_write_sum', full_name='OssOverviewRet.disk_write_sum', index=4,
      number=5, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_info', full_name='OssOverviewRet.node_info', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_perf_read', full_name='OssOverviewRet.disk_perf_read', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_perf_average_read', full_name='OssOverviewRet.disk_perf_average_read', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_perf_write', full_name='OssOverviewRet.disk_perf_write', index=8,
      number=9, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disk_per_average_write', full_name='OssOverviewRet.disk_per_average_write', index=9,
      number=10, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=713,
  serialized_end=1045,
)


_NODELISTPARA = _descriptor.Descriptor(
  name='NodeListPara',
  full_name='NodeListPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='client', full_name='NodeListPara.client', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='hide_internal_ips', full_name='NodeListPara.hide_internal_ips', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='agent', full_name='NodeListPara.agent', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1047,
  serialized_end=1119,
)


_NODEINFO = _descriptor.Descriptor(
  name='NodeInfo',
  full_name='NodeInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='NodeInfo.type', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_num_id', full_name='NodeInfo.node_num_id', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_name', full_name='NodeInfo.node_name', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1121,
  serialized_end=1185,
)


_NODELISTRET = _descriptor.Descriptor(
  name='NodeListRet',
  full_name='NodeListRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='node_lists', full_name='NodeListRet.node_lists', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1187,
  serialized_end=1231,
)

_MDSOVERVIEWRET.fields_by_name['node_info'].message_type = _SERVERNODE
_MDSOVERVIEWRET.fields_by_name['work_requests'].message_type = _TIMEVALUE
_MDSOVERVIEWRET.fields_by_name['queued_requests'].message_type = _TIMEVALUE
_OSSOVERVIEWRET.fields_by_name['node_info'].message_type = _SERVERNODE
_OSSOVERVIEWRET.fields_by_name['disk_perf_read'].message_type = _TIMEVALUE
_OSSOVERVIEWRET.fields_by_name['disk_perf_average_read'].message_type = _TIMEVALUE
_OSSOVERVIEWRET.fields_by_name['disk_perf_write'].message_type = _TIMEVALUE
_OSSOVERVIEWRET.fields_by_name['disk_per_average_write'].message_type = _TIMEVALUE
_NODELISTRET.fields_by_name['node_lists'].message_type = _NODEINFO
DESCRIPTOR.message_types_by_name['ClientStatsPara'] = _CLIENTSTATSPARA
DESCRIPTOR.message_types_by_name['ClientStatsRet'] = _CLIENTSTATSRET
DESCRIPTOR.message_types_by_name['GetSlaInfoPara'] = _GETSLAINFOPARA
DESCRIPTOR.message_types_by_name['GetSlaInfoRet'] = _GETSLAINFORET
DESCRIPTOR.message_types_by_name['TimeValue'] = _TIMEVALUE
DESCRIPTOR.message_types_by_name['ServerNode'] = _SERVERNODE
DESCRIPTOR.message_types_by_name['MdsOverviewPara'] = _MDSOVERVIEWPARA
DESCRIPTOR.message_types_by_name['MdsOverviewRet'] = _MDSOVERVIEWRET
DESCRIPTOR.message_types_by_name['OssOverviewPara'] = _OSSOVERVIEWPARA
DESCRIPTOR.message_types_by_name['OssOverviewRet'] = _OSSOVERVIEWRET
DESCRIPTOR.message_types_by_name['NodeListPara'] = _NODELISTPARA
DESCRIPTOR.message_types_by_name['NodeInfo'] = _NODEINFO
DESCRIPTOR.message_types_by_name['NodeListRet'] = _NODELISTRET
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ClientStatsPara = _reflection.GeneratedProtocolMessageType('ClientStatsPara', (_message.Message,), {
  'DESCRIPTOR' : _CLIENTSTATSPARA,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:ClientStatsPara)
  })
_sym_db.RegisterMessage(ClientStatsPara)

ClientStatsRet = _reflection.GeneratedProtocolMessageType('ClientStatsRet', (_message.Message,), {
  'DESCRIPTOR' : _CLIENTSTATSRET,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:ClientStatsRet)
  })
_sym_db.RegisterMessage(ClientStatsRet)

GetSlaInfoPara = _reflection.GeneratedProtocolMessageType('GetSlaInfoPara', (_message.Message,), {
  'DESCRIPTOR' : _GETSLAINFOPARA,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:GetSlaInfoPara)
  })
_sym_db.RegisterMessage(GetSlaInfoPara)

GetSlaInfoRet = _reflection.GeneratedProtocolMessageType('GetSlaInfoRet', (_message.Message,), {
  'DESCRIPTOR' : _GETSLAINFORET,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:GetSlaInfoRet)
  })
_sym_db.RegisterMessage(GetSlaInfoRet)

TimeValue = _reflection.GeneratedProtocolMessageType('TimeValue', (_message.Message,), {
  'DESCRIPTOR' : _TIMEVALUE,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:TimeValue)
  })
_sym_db.RegisterMessage(TimeValue)

ServerNode = _reflection.GeneratedProtocolMessageType('ServerNode', (_message.Message,), {
  'DESCRIPTOR' : _SERVERNODE,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:ServerNode)
  })
_sym_db.RegisterMessage(ServerNode)

MdsOverviewPara = _reflection.GeneratedProtocolMessageType('MdsOverviewPara', (_message.Message,), {
  'DESCRIPTOR' : _MDSOVERVIEWPARA,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:MdsOverviewPara)
  })
_sym_db.RegisterMessage(MdsOverviewPara)

MdsOverviewRet = _reflection.GeneratedProtocolMessageType('MdsOverviewRet', (_message.Message,), {
  'DESCRIPTOR' : _MDSOVERVIEWRET,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:MdsOverviewRet)
  })
_sym_db.RegisterMessage(MdsOverviewRet)

OssOverviewPara = _reflection.GeneratedProtocolMessageType('OssOverviewPara', (_message.Message,), {
  'DESCRIPTOR' : _OSSOVERVIEWPARA,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:OssOverviewPara)
  })
_sym_db.RegisterMessage(OssOverviewPara)

OssOverviewRet = _reflection.GeneratedProtocolMessageType('OssOverviewRet', (_message.Message,), {
  'DESCRIPTOR' : _OSSOVERVIEWRET,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:OssOverviewRet)
  })
_sym_db.RegisterMessage(OssOverviewRet)

NodeListPara = _reflection.GeneratedProtocolMessageType('NodeListPara', (_message.Message,), {
  'DESCRIPTOR' : _NODELISTPARA,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:NodeListPara)
  })
_sym_db.RegisterMessage(NodeListPara)

NodeInfo = _reflection.GeneratedProtocolMessageType('NodeInfo', (_message.Message,), {
  'DESCRIPTOR' : _NODEINFO,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:NodeInfo)
  })
_sym_db.RegisterMessage(NodeInfo)

NodeListRet = _reflection.GeneratedProtocolMessageType('NodeListRet', (_message.Message,), {
  'DESCRIPTOR' : _NODELISTRET,
  '__module__' : 'agent_pb2'
  # @@protoc_insertion_point(class_scope:NodeListRet)
  })
_sym_db.RegisterMessage(NodeListRet)



_AGENT = _descriptor.ServiceDescriptor(
  name='Agent',
  full_name='Agent',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=1234,
  serialized_end=1495,
  methods=[
  _descriptor.MethodDescriptor(
    name='ClientStats',
    full_name='Agent.ClientStats',
    index=0,
    containing_service=None,
    input_type=_CLIENTSTATSPARA,
    output_type=_CLIENTSTATSRET,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetSlaInfo',
    full_name='Agent.GetSlaInfo',
    index=1,
    containing_service=None,
    input_type=_GETSLAINFOPARA,
    output_type=_GETSLAINFORET,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='MdsOverview',
    full_name='Agent.MdsOverview',
    index=2,
    containing_service=None,
    input_type=_MDSOVERVIEWPARA,
    output_type=_MDSOVERVIEWRET,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='OssOverview',
    full_name='Agent.OssOverview',
    index=3,
    containing_service=None,
    input_type=_OSSOVERVIEWPARA,
    output_type=_OSSOVERVIEWRET,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='NodeList',
    full_name='Agent.NodeList',
    index=4,
    containing_service=None,
    input_type=_NODELISTPARA,
    output_type=_NODELISTRET,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_AGENT)

DESCRIPTOR.services_by_name['Agent'] = _AGENT

# @@protoc_insertion_point(module_scope)
