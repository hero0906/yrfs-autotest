# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: setentry.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import common.grpc.response_pb2 as response__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0esetentry.proto\x12\tYrcfAgent\x1a\x0eresponse.proto\"\xe9\x01\n\x0fSetEntryRequest\x12\x18\n\x10use_mounted_path\x18\x01 \x01(\x08\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x13\n\x0bstripe_size\x18\x03 \x01(\t\x12\x14\n\x0cstripe_count\x18\x04 \x01(\r\x12\x31\n\x06schema\x18\x05 \x01(\x0e\x32!.YrcfAgent.SetEntryRequest.Schema\x12\x0f\n\x07pool_id\x18\x06 \x01(\t\x12\x11\n\tforce_set\x18\x07 \x01(\x08\",\n\x06Schema\x12\n\n\x06MIRROR\x10\x00\x12\t\n\x05RAID0\x10\x01\x12\x0b\n\x07STANDBY\x10\x02\"5\n\x10SetEntryResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes2O\n\x08SetEntry\x12\x43\n\x08SetEntry\x12\x1a.YrcfAgent.SetEntryRequest\x1a\x1b.YrcfAgent.SetEntryResponseb\x06proto3')



_SETENTRYREQUEST = DESCRIPTOR.message_types_by_name['SetEntryRequest']
_SETENTRYRESPONSE = DESCRIPTOR.message_types_by_name['SetEntryResponse']
_SETENTRYREQUEST_SCHEMA = _SETENTRYREQUEST.enum_types_by_name['Schema']
SetEntryRequest = _reflection.GeneratedProtocolMessageType('SetEntryRequest', (_message.Message,), {
  'DESCRIPTOR' : _SETENTRYREQUEST,
  '__module__' : 'setentry_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.SetEntryRequest)
  })
_sym_db.RegisterMessage(SetEntryRequest)

SetEntryResponse = _reflection.GeneratedProtocolMessageType('SetEntryResponse', (_message.Message,), {
  'DESCRIPTOR' : _SETENTRYRESPONSE,
  '__module__' : 'setentry_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.SetEntryResponse)
  })
_sym_db.RegisterMessage(SetEntryResponse)

_SETENTRY = DESCRIPTOR.services_by_name['SetEntry']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SETENTRYREQUEST._serialized_start=46
  _SETENTRYREQUEST._serialized_end=279
  _SETENTRYREQUEST_SCHEMA._serialized_start=235
  _SETENTRYREQUEST_SCHEMA._serialized_end=279
  _SETENTRYRESPONSE._serialized_start=281
  _SETENTRYRESPONSE._serialized_end=334
  _SETENTRY._serialized_start=336
  _SETENTRY._serialized_end=415
# @@protoc_insertion_point(module_scope)
