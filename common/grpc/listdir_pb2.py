# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: listdir.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import response_pb2 as response__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='listdir.proto',
  package='YrcfAgent',
  syntax='proto3',
  serialized_pb=_b('\n\rlistdir.proto\x12\tYrcfAgent\x1a\x0eresponse.proto\",\n\x0bListDirPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0f\n\x07mounted\x18\x02 \x01(\x08\"7\n\x0bListDirInfo\x12\x13\n\x0b\x65ntry_types\x18\x01 \x01(\t\x12\x13\n\x0b\x65ntry_names\x18\x02 \x01(\t\"?\n\nListDirRet\x12\x31\n\x11listdir_info_list\x18\x01 \x03(\x0b\x32\x16.YrcfAgent.ListDirInfo\"Z\n\x0fListDirResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\x12$\n\x05value\x18\x02 \x01(\x0b\x32\x15.YrcfAgent.ListDirRet2J\n\x07ListDir\x12?\n\x07ListDir\x12\x16.YrcfAgent.ListDirPara\x1a\x1a.YrcfAgent.ListDirResponse\"\x00\x62\x06proto3')
  ,
  dependencies=[response__pb2.DESCRIPTOR,])




_LISTDIRPARA = _descriptor.Descriptor(
  name='ListDirPara',
  full_name='YrcfAgent.ListDirPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.ListDirPara.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='mounted', full_name='YrcfAgent.ListDirPara.mounted', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=44,
  serialized_end=88,
)


_LISTDIRINFO = _descriptor.Descriptor(
  name='ListDirInfo',
  full_name='YrcfAgent.ListDirInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='entry_types', full_name='YrcfAgent.ListDirInfo.entry_types', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='entry_names', full_name='YrcfAgent.ListDirInfo.entry_names', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=90,
  serialized_end=145,
)


_LISTDIRRET = _descriptor.Descriptor(
  name='ListDirRet',
  full_name='YrcfAgent.ListDirRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='listdir_info_list', full_name='YrcfAgent.ListDirRet.listdir_info_list', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=147,
  serialized_end=210,
)


_LISTDIRRESPONSE = _descriptor.Descriptor(
  name='ListDirResponse',
  full_name='YrcfAgent.ListDirResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='YrcfAgent.ListDirResponse.result', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='YrcfAgent.ListDirResponse.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=212,
  serialized_end=302,
)

_LISTDIRRET.fields_by_name['listdir_info_list'].message_type = _LISTDIRINFO
_LISTDIRRESPONSE.fields_by_name['result'].message_type = response__pb2._RESMES
_LISTDIRRESPONSE.fields_by_name['value'].message_type = _LISTDIRRET
DESCRIPTOR.message_types_by_name['ListDirPara'] = _LISTDIRPARA
DESCRIPTOR.message_types_by_name['ListDirInfo'] = _LISTDIRINFO
DESCRIPTOR.message_types_by_name['ListDirRet'] = _LISTDIRRET
DESCRIPTOR.message_types_by_name['ListDirResponse'] = _LISTDIRRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ListDirPara = _reflection.GeneratedProtocolMessageType('ListDirPara', (_message.Message,), dict(
  DESCRIPTOR = _LISTDIRPARA,
  __module__ = 'listdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListDirPara)
  ))
_sym_db.RegisterMessage(ListDirPara)

ListDirInfo = _reflection.GeneratedProtocolMessageType('ListDirInfo', (_message.Message,), dict(
  DESCRIPTOR = _LISTDIRINFO,
  __module__ = 'listdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListDirInfo)
  ))
_sym_db.RegisterMessage(ListDirInfo)

ListDirRet = _reflection.GeneratedProtocolMessageType('ListDirRet', (_message.Message,), dict(
  DESCRIPTOR = _LISTDIRRET,
  __module__ = 'listdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListDirRet)
  ))
_sym_db.RegisterMessage(ListDirRet)

ListDirResponse = _reflection.GeneratedProtocolMessageType('ListDirResponse', (_message.Message,), dict(
  DESCRIPTOR = _LISTDIRRESPONSE,
  __module__ = 'listdir_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListDirResponse)
  ))
_sym_db.RegisterMessage(ListDirResponse)



_LISTDIR = _descriptor.ServiceDescriptor(
  name='ListDir',
  full_name='YrcfAgent.ListDir',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=304,
  serialized_end=378,
  methods=[
  _descriptor.MethodDescriptor(
    name='ListDir',
    full_name='YrcfAgent.ListDir.ListDir',
    index=0,
    containing_service=None,
    input_type=_LISTDIRPARA,
    output_type=_LISTDIRRESPONSE,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_LISTDIR)

DESCRIPTOR.services_by_name['ListDir'] = _LISTDIR

# @@protoc_insertion_point(module_scope)