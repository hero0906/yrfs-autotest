# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mkdir.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import common.grpc.response_pb2 as response__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bmkdir.proto\x12\tYrcfAgent\x1a\x0eresponse.proto\"\xa4\x01\n\x0cMkDirRequest\x12\x19\n\x11use_absolute_path\x18\x01 \x01(\x08\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x12\n\nprefer_mds\x18\x03 \x01(\t\x12\x13\n\x0b\x61\x63\x63\x65ss_mode\x18\x04 \x01(\t\x12\x0b\n\x03uid\x18\x05 \x01(\x04\x12\x0b\n\x03gid\x18\x06 \x01(\x04\x12\x16\n\x0enot_use_mirror\x18\x07 \x01(\x08\x12\x10\n\x08\x63\x61sefold\x18\x08 \x01(\x08\"2\n\rMkDirResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes2E\n\x05MkDir\x12<\n\x05MkDir\x12\x17.YrcfAgent.MkDirRequest\x1a\x18.YrcfAgent.MkDirResponse\"\x00\x62\x06proto3')



_MKDIRREQUEST = DESCRIPTOR.message_types_by_name['MkDirRequest']
_MKDIRRESPONSE = DESCRIPTOR.message_types_by_name['MkDirResponse']
MkDirRequest = _reflection.GeneratedProtocolMessageType('MkDirRequest', (_message.Message,), {
  'DESCRIPTOR' : _MKDIRREQUEST,
  '__module__' : 'mkdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.MkDirRequest)
  })
_sym_db.RegisterMessage(MkDirRequest)

MkDirResponse = _reflection.GeneratedProtocolMessageType('MkDirResponse', (_message.Message,), {
  'DESCRIPTOR' : _MKDIRRESPONSE,
  '__module__' : 'mkdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.MkDirResponse)
  })
_sym_db.RegisterMessage(MkDirResponse)

_MKDIR = DESCRIPTOR.services_by_name['MkDir']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _MKDIRREQUEST._serialized_start=43
  _MKDIRREQUEST._serialized_end=207
  _MKDIRRESPONSE._serialized_start=209
  _MKDIRRESPONSE._serialized_end=259
  _MKDIR._serialized_start=261
  _MKDIR._serialized_end=330
# @@protoc_insertion_point(module_scope)
