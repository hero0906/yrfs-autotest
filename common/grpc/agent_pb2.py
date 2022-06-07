# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: agent.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x61gent.proto\"u\n\x0f\x43lientStatsPara\x12\x11\n\tnode_type\x18\x01 \x01(\r\x12\x19\n\x11hide_internal_ips\x18\x02 \x01(\x08\x12\x19\n\x11return_zero_stats\x18\x03 \x01(\x08\x12\x19\n\x11\x63lient_stats_type\x18\x04 \x01(\r\"@\n\x0e\x43lientStatsRet\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0e\n\x06online\x18\x02 \x01(\x08\x12\x12\n\nopcounters\x18\x03 \x03(\x04\"#\n\x0eGetSlaInfoPara\x12\x11\n\twith_root\x18\x01 \x01(\x08\"B\n\rGetSlaInfoRet\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x10\n\x08\x65ntry_id\x18\x02 \x01(\t\x12\x11\n\tsla_value\x18\x03 \x03(\x04\"(\n\tTimeValue\x12\x0c\n\x04time\x18\x01 \x01(\x04\x12\r\n\x05value\x18\x02 \x01(\x04\"D\n\nServerNode\x12\x11\n\tnode_name\x18\x01 \x01(\t\x12\x13\n\x0bnode_num_id\x18\x02 \x01(\r\x12\x0e\n\x06online\x18\x03 \x01(\x08\"!\n\x0fMdsOverviewPara\x12\x0e\n\x06unused\x18\x01 \x01(\x08\"\xde\x01\n\x0eMdsOverviewRet\x12\x18\n\x10\x64isk_space_total\x18\x01 \x01(\x04\x12\x17\n\x0f\x64isk_space_free\x18\x02 \x01(\x04\x12\x17\n\x0f\x64isk_space_used\x18\x03 \x01(\x04\x12\x18\n\x10inode_space_used\x18\x04 \x01(\x04\x12\x1e\n\tnode_info\x18\x05 \x03(\x0b\x32\x0b.ServerNode\x12!\n\rwork_requests\x18\x06 \x03(\x0b\x32\n.TimeValue\x12#\n\x0fqueued_requests\x18\x07 \x03(\x0b\x32\n.TimeValue\"!\n\x0fOssOverviewPara\x12\x0e\n\x06unused\x18\x01 \x01(\x08\"\xcc\x02\n\x0eOssOverviewRet\x12\x18\n\x10\x64isk_space_total\x18\x01 \x01(\x04\x12\x17\n\x0f\x64isk_space_free\x18\x02 \x01(\x04\x12\x17\n\x0f\x64isk_space_used\x18\x03 \x01(\x04\x12\x15\n\rdisk_read_sum\x18\x04 \x01(\x04\x12\x16\n\x0e\x64isk_write_sum\x18\x05 \x01(\x04\x12\x1e\n\tnode_info\x18\x06 \x03(\x0b\x32\x0b.ServerNode\x12\"\n\x0e\x64isk_perf_read\x18\x07 \x03(\x0b\x32\n.TimeValue\x12*\n\x16\x64isk_perf_average_read\x18\x08 \x03(\x0b\x32\n.TimeValue\x12#\n\x0f\x64isk_perf_write\x18\t \x03(\x0b\x32\n.TimeValue\x12*\n\x16\x64isk_per_average_write\x18\n \x03(\x0b\x32\n.TimeValue\"H\n\x0cNodeListPara\x12\x0e\n\x06\x63lient\x18\x01 \x01(\x08\x12\x19\n\x11hide_internal_ips\x18\x02 \x01(\x08\x12\r\n\x05\x61gent\x18\x03 \x01(\x08\"@\n\x08NodeInfo\x12\x0c\n\x04type\x18\x01 \x01(\r\x12\x13\n\x0bnode_num_id\x18\x02 \x01(\r\x12\x11\n\tnode_name\x18\x03 \x01(\t\",\n\x0bNodeListRet\x12\x1d\n\nnode_lists\x18\x01 \x03(\x0b\x32\t.NodeInfo2\x85\x02\n\x05\x41gent\x12\x34\n\x0b\x43lientStats\x12\x10.ClientStatsPara\x1a\x0f.ClientStatsRet\"\x00\x30\x01\x12\x31\n\nGetSlaInfo\x12\x0f.GetSlaInfoPara\x1a\x0e.GetSlaInfoRet\"\x00\x30\x01\x12\x32\n\x0bMdsOverview\x12\x10.MdsOverviewPara\x1a\x0f.MdsOverviewRet\"\x00\x12\x32\n\x0bOssOverview\x12\x10.OssOverviewPara\x1a\x0f.OssOverviewRet\"\x00\x12+\n\x08NodeList\x12\r.NodeListPara\x1a\x0c.NodeListRet\"\x00\x30\x01\x62\x06proto3')



_CLIENTSTATSPARA = DESCRIPTOR.message_types_by_name['ClientStatsPara']
_CLIENTSTATSRET = DESCRIPTOR.message_types_by_name['ClientStatsRet']
_GETSLAINFOPARA = DESCRIPTOR.message_types_by_name['GetSlaInfoPara']
_GETSLAINFORET = DESCRIPTOR.message_types_by_name['GetSlaInfoRet']
_TIMEVALUE = DESCRIPTOR.message_types_by_name['TimeValue']
_SERVERNODE = DESCRIPTOR.message_types_by_name['ServerNode']
_MDSOVERVIEWPARA = DESCRIPTOR.message_types_by_name['MdsOverviewPara']
_MDSOVERVIEWRET = DESCRIPTOR.message_types_by_name['MdsOverviewRet']
_OSSOVERVIEWPARA = DESCRIPTOR.message_types_by_name['OssOverviewPara']
_OSSOVERVIEWRET = DESCRIPTOR.message_types_by_name['OssOverviewRet']
_NODELISTPARA = DESCRIPTOR.message_types_by_name['NodeListPara']
_NODEINFO = DESCRIPTOR.message_types_by_name['NodeInfo']
_NODELISTRET = DESCRIPTOR.message_types_by_name['NodeListRet']
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

_AGENT = DESCRIPTOR.services_by_name['Agent']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLIENTSTATSPARA._serialized_start=15
  _CLIENTSTATSPARA._serialized_end=132
  _CLIENTSTATSRET._serialized_start=134
  _CLIENTSTATSRET._serialized_end=198
  _GETSLAINFOPARA._serialized_start=200
  _GETSLAINFOPARA._serialized_end=235
  _GETSLAINFORET._serialized_start=237
  _GETSLAINFORET._serialized_end=303
  _TIMEVALUE._serialized_start=305
  _TIMEVALUE._serialized_end=345
  _SERVERNODE._serialized_start=347
  _SERVERNODE._serialized_end=415
  _MDSOVERVIEWPARA._serialized_start=417
  _MDSOVERVIEWPARA._serialized_end=450
  _MDSOVERVIEWRET._serialized_start=453
  _MDSOVERVIEWRET._serialized_end=675
  _OSSOVERVIEWPARA._serialized_start=677
  _OSSOVERVIEWPARA._serialized_end=710
  _OSSOVERVIEWRET._serialized_start=713
  _OSSOVERVIEWRET._serialized_end=1045
  _NODELISTPARA._serialized_start=1047
  _NODELISTPARA._serialized_end=1119
  _NODEINFO._serialized_start=1121
  _NODEINFO._serialized_end=1185
  _NODELISTRET._serialized_start=1187
  _NODELISTRET._serialized_end=1231
  _AGENT._serialized_start=1234
  _AGENT._serialized_end=1495
# @@protoc_insertion_point(module_scope)
