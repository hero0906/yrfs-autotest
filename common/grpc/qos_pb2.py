# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: qos.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import response_pb2 as response__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tqos.proto\x12\tYrcfAgent\x1a\x0eresponse.proto\"\x7f\n\nAddQosPara\x12\x0c\n\x04rbps\x18\x01 \x01(\x04\x12\x0c\n\x04wbps\x18\x02 \x01(\x04\x12\r\n\x05riops\x18\x03 \x01(\x04\x12\r\n\x05wiops\x18\x04 \x01(\x04\x12\x0c\n\x04tbps\x18\x05 \x01(\x04\x12\r\n\x05tiops\x18\x06 \x01(\x04\x12\x0c\n\x04mops\x18\x07 \x01(\x04\x12\x0c\n\x04path\x18\x08 \x01(\t\"3\n\x0e\x41\x64\x64QosResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\"+\n\x0bListQosPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0e\n\x06prefix\x18\x02 \x01(\x08\"\x89\x01\n\x07QosInfo\x12\x0b\n\x03\x65id\x18\x01 \x01(\t\x12\x0c\n\x04rbps\x18\x02 \x01(\x04\x12\x0c\n\x04wbps\x18\x03 \x01(\x04\x12\r\n\x05riops\x18\x04 \x01(\x04\x12\r\n\x05wiops\x18\x05 \x01(\x04\x12\x0c\n\x04tbps\x18\x06 \x01(\x04\x12\r\n\x05tiops\x18\x07 \x01(\x04\x12\x0c\n\x04mops\x18\x08 \x01(\x04\x12\x0c\n\x04path\x18\t \x01(\t\"7\n\nQosInfoRet\x12)\n\rqos_info_list\x18\x01 \x03(\x0b\x32\x12.YrcfAgent.QosInfo\"Z\n\x0fListQosResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\x12$\n\x05value\x18\x02 \x01(\x0b\x32\x15.YrcfAgent.QosInfoRet\"?\n\rDeleteQosPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x11\n\trecursive\x18\x02 \x01(\x08\x12\r\n\x05\x66orce\x18\x03 \x01(\x08\"6\n\x11\x44\x65leteQosResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes2\xcb\x01\n\x03Qos\x12<\n\x06\x41\x64\x64Qos\x12\x15.YrcfAgent.AddQosPara\x1a\x19.YrcfAgent.AddQosResponse\"\x00\x12\x45\n\tDeleteQos\x12\x18.YrcfAgent.DeleteQosPara\x1a\x1c.YrcfAgent.DeleteQosResponse\"\x00\x12?\n\x07ListQos\x12\x16.YrcfAgent.ListQosPara\x1a\x1a.YrcfAgent.ListQosResponse\"\x00\x62\x06proto3')



_ADDQOSPARA = DESCRIPTOR.message_types_by_name['AddQosPara']
_ADDQOSRESPONSE = DESCRIPTOR.message_types_by_name['AddQosResponse']
_LISTQOSPARA = DESCRIPTOR.message_types_by_name['ListQosPara']
_QOSINFO = DESCRIPTOR.message_types_by_name['QosInfo']
_QOSINFORET = DESCRIPTOR.message_types_by_name['QosInfoRet']
_LISTQOSRESPONSE = DESCRIPTOR.message_types_by_name['ListQosResponse']
_DELETEQOSPARA = DESCRIPTOR.message_types_by_name['DeleteQosPara']
_DELETEQOSRESPONSE = DESCRIPTOR.message_types_by_name['DeleteQosResponse']
AddQosPara = _reflection.GeneratedProtocolMessageType('AddQosPara', (_message.Message,), {
  'DESCRIPTOR' : _ADDQOSPARA,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.AddQosPara)
  })
_sym_db.RegisterMessage(AddQosPara)

AddQosResponse = _reflection.GeneratedProtocolMessageType('AddQosResponse', (_message.Message,), {
  'DESCRIPTOR' : _ADDQOSRESPONSE,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.AddQosResponse)
  })
_sym_db.RegisterMessage(AddQosResponse)

ListQosPara = _reflection.GeneratedProtocolMessageType('ListQosPara', (_message.Message,), {
  'DESCRIPTOR' : _LISTQOSPARA,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListQosPara)
  })
_sym_db.RegisterMessage(ListQosPara)

QosInfo = _reflection.GeneratedProtocolMessageType('QosInfo', (_message.Message,), {
  'DESCRIPTOR' : _QOSINFO,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.QosInfo)
  })
_sym_db.RegisterMessage(QosInfo)

QosInfoRet = _reflection.GeneratedProtocolMessageType('QosInfoRet', (_message.Message,), {
  'DESCRIPTOR' : _QOSINFORET,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.QosInfoRet)
  })
_sym_db.RegisterMessage(QosInfoRet)

ListQosResponse = _reflection.GeneratedProtocolMessageType('ListQosResponse', (_message.Message,), {
  'DESCRIPTOR' : _LISTQOSRESPONSE,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListQosResponse)
  })
_sym_db.RegisterMessage(ListQosResponse)

DeleteQosPara = _reflection.GeneratedProtocolMessageType('DeleteQosPara', (_message.Message,), {
  'DESCRIPTOR' : _DELETEQOSPARA,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.DeleteQosPara)
  })
_sym_db.RegisterMessage(DeleteQosPara)

DeleteQosResponse = _reflection.GeneratedProtocolMessageType('DeleteQosResponse', (_message.Message,), {
  'DESCRIPTOR' : _DELETEQOSRESPONSE,
  '__module__' : 'qos_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.DeleteQosResponse)
  })
_sym_db.RegisterMessage(DeleteQosResponse)

_QOS = DESCRIPTOR.services_by_name['Qos']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ADDQOSPARA._serialized_start=40
  _ADDQOSPARA._serialized_end=167
  _ADDQOSRESPONSE._serialized_start=169
  _ADDQOSRESPONSE._serialized_end=220
  _LISTQOSPARA._serialized_start=222
  _LISTQOSPARA._serialized_end=265
  _QOSINFO._serialized_start=268
  _QOSINFO._serialized_end=405
  _QOSINFORET._serialized_start=407
  _QOSINFORET._serialized_end=462
  _LISTQOSRESPONSE._serialized_start=464
  _LISTQOSRESPONSE._serialized_end=554
  _DELETEQOSPARA._serialized_start=556
  _DELETEQOSPARA._serialized_end=619
  _DELETEQOSRESPONSE._serialized_start=621
  _DELETEQOSRESPONSE._serialized_end=675
  _QOS._serialized_start=678
  _QOS._serialized_end=881
# @@protoc_insertion_point(module_scope)
