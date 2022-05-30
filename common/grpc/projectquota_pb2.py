# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: projectquota.proto

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
  name='projectquota.proto',
  package='YrcfAgent',
  syntax='proto3',
  serialized_pb=_b('\n\x12projectquota.proto\x12\tYrcfAgent\x1a\x0eresponse.proto\"\x8a\x01\n\x13\x41\x64\x64ProjectQuotaPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x12\n\nspacelimit\x18\x02 \x01(\x04\x12\x12\n\ninodelimit\x18\x03 \x01(\x04\x12\x11\n\trecursive\x18\x04 \x01(\x08\x12\x16\n\x0eignoreexisting\x18\x05 \x01(\x08\x12\x12\n\npjcontinue\x18\x06 \x01(\x08\"<\n\x17\x41\x64\x64ProjectQuotaResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\"4\n\x14ListProjectQuotaPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0e\n\x06prefix\x18\x02 \x01(\x08\"\xb6\x01\n\x10ProjectQuotaInfo\x12\x0b\n\x03\x65id\x18\x01 \x01(\t\x12\x16\n\x0eprojectquotaid\x18\x02 \x01(\x04\x12\x11\n\tspaceused\x18\x03 \x01(\x04\x12\x12\n\nspacelimit\x18\x04 \x01(\x04\x12\x11\n\tinodeused\x18\x05 \x01(\x04\x12\x12\n\ninodelimit\x18\x06 \x01(\x04\x12\x0f\n\x07\x64irused\x18\x07 \x01(\x04\x12\x10\n\x08\x66ileused\x18\x08 \x01(\x04\x12\x0c\n\x04path\x18\t \x01(\t\"O\n\x0fProjectQuotaRet\x12<\n\x17project_quota_info_list\x18\x01 \x03(\x0b\x32\x1b.YrcfAgent.ProjectQuotaInfo\"h\n\x18ListProjectQuotaResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\x12)\n\x05value\x18\x02 \x01(\x0b\x32\x1a.YrcfAgent.ProjectQuotaRet\"B\n\x16\x44\x65leteProjectQuotaPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0b\n\x03\x65id\x18\x02 \x01(\t\x12\r\n\x05\x66orce\x18\x03 \x01(\x08\"?\n\x1a\x44\x65leteProjectQuotaResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes\"N\n\x16UpdateProjectQuotaPara\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x12\n\nspacelimit\x18\x02 \x01(\x04\x12\x12\n\ninodelimit\x18\x03 \x01(\x04\"?\n\x1aUpdateProjectQuotaResponse\x12!\n\x06result\x18\x01 \x01(\x0b\x32\x11.YrcfAgent.ResMes2\x87\x03\n\x0cProjectQuota\x12W\n\x0f\x41\x64\x64ProjectQuota\x12\x1e.YrcfAgent.AddProjectQuotaPara\x1a\".YrcfAgent.AddProjectQuotaResponse\"\x00\x12Z\n\x10ListProjectQuota\x12\x1f.YrcfAgent.ListProjectQuotaPara\x1a#.YrcfAgent.ListProjectQuotaResponse\"\x00\x12`\n\x12\x44\x65leteProjectQuota\x12!.YrcfAgent.DeleteProjectQuotaPara\x1a%.YrcfAgent.DeleteProjectQuotaResponse\"\x00\x12`\n\x12UpdateProjectQuota\x12!.YrcfAgent.UpdateProjectQuotaPara\x1a%.YrcfAgent.UpdateProjectQuotaResponse\"\x00\x62\x06proto3')
  ,
  dependencies=[response__pb2.DESCRIPTOR,])




_ADDPROJECTQUOTAPARA = _descriptor.Descriptor(
  name='AddProjectQuotaPara',
  full_name='YrcfAgent.AddProjectQuotaPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.AddProjectQuotaPara.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='spacelimit', full_name='YrcfAgent.AddProjectQuotaPara.spacelimit', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='inodelimit', full_name='YrcfAgent.AddProjectQuotaPara.inodelimit', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='recursive', full_name='YrcfAgent.AddProjectQuotaPara.recursive', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ignoreexisting', full_name='YrcfAgent.AddProjectQuotaPara.ignoreexisting', index=4,
      number=5, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pjcontinue', full_name='YrcfAgent.AddProjectQuotaPara.pjcontinue', index=5,
      number=6, type=8, cpp_type=7, label=1,
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
  serialized_start=50,
  serialized_end=188,
)


_ADDPROJECTQUOTARESPONSE = _descriptor.Descriptor(
  name='AddProjectQuotaResponse',
  full_name='YrcfAgent.AddProjectQuotaResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='YrcfAgent.AddProjectQuotaResponse.result', index=0,
      number=1, type=11, cpp_type=10, label=1,
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
  serialized_start=190,
  serialized_end=250,
)


_LISTPROJECTQUOTAPARA = _descriptor.Descriptor(
  name='ListProjectQuotaPara',
  full_name='YrcfAgent.ListProjectQuotaPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.ListProjectQuotaPara.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='prefix', full_name='YrcfAgent.ListProjectQuotaPara.prefix', index=1,
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
  serialized_start=252,
  serialized_end=304,
)


_PROJECTQUOTAINFO = _descriptor.Descriptor(
  name='ProjectQuotaInfo',
  full_name='YrcfAgent.ProjectQuotaInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='eid', full_name='YrcfAgent.ProjectQuotaInfo.eid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='projectquotaid', full_name='YrcfAgent.ProjectQuotaInfo.projectquotaid', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='spaceused', full_name='YrcfAgent.ProjectQuotaInfo.spaceused', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='spacelimit', full_name='YrcfAgent.ProjectQuotaInfo.spacelimit', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='inodeused', full_name='YrcfAgent.ProjectQuotaInfo.inodeused', index=4,
      number=5, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='inodelimit', full_name='YrcfAgent.ProjectQuotaInfo.inodelimit', index=5,
      number=6, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dirused', full_name='YrcfAgent.ProjectQuotaInfo.dirused', index=6,
      number=7, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileused', full_name='YrcfAgent.ProjectQuotaInfo.fileused', index=7,
      number=8, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.ProjectQuotaInfo.path', index=8,
      number=9, type=9, cpp_type=9, label=1,
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
  serialized_start=307,
  serialized_end=489,
)


_PROJECTQUOTARET = _descriptor.Descriptor(
  name='ProjectQuotaRet',
  full_name='YrcfAgent.ProjectQuotaRet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='project_quota_info_list', full_name='YrcfAgent.ProjectQuotaRet.project_quota_info_list', index=0,
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
  serialized_start=491,
  serialized_end=570,
)


_LISTPROJECTQUOTARESPONSE = _descriptor.Descriptor(
  name='ListProjectQuotaResponse',
  full_name='YrcfAgent.ListProjectQuotaResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='YrcfAgent.ListProjectQuotaResponse.result', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='YrcfAgent.ListProjectQuotaResponse.value', index=1,
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
  serialized_start=572,
  serialized_end=676,
)


_DELETEPROJECTQUOTAPARA = _descriptor.Descriptor(
  name='DeleteProjectQuotaPara',
  full_name='YrcfAgent.DeleteProjectQuotaPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.DeleteProjectQuotaPara.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='eid', full_name='YrcfAgent.DeleteProjectQuotaPara.eid', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='force', full_name='YrcfAgent.DeleteProjectQuotaPara.force', index=2,
      number=3, type=8, cpp_type=7, label=1,
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
  serialized_start=678,
  serialized_end=744,
)


_DELETEPROJECTQUOTARESPONSE = _descriptor.Descriptor(
  name='DeleteProjectQuotaResponse',
  full_name='YrcfAgent.DeleteProjectQuotaResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='YrcfAgent.DeleteProjectQuotaResponse.result', index=0,
      number=1, type=11, cpp_type=10, label=1,
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
  serialized_start=746,
  serialized_end=809,
)


_UPDATEPROJECTQUOTAPARA = _descriptor.Descriptor(
  name='UpdateProjectQuotaPara',
  full_name='YrcfAgent.UpdateProjectQuotaPara',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='YrcfAgent.UpdateProjectQuotaPara.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='spacelimit', full_name='YrcfAgent.UpdateProjectQuotaPara.spacelimit', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='inodelimit', full_name='YrcfAgent.UpdateProjectQuotaPara.inodelimit', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=811,
  serialized_end=889,
)


_UPDATEPROJECTQUOTARESPONSE = _descriptor.Descriptor(
  name='UpdateProjectQuotaResponse',
  full_name='YrcfAgent.UpdateProjectQuotaResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='YrcfAgent.UpdateProjectQuotaResponse.result', index=0,
      number=1, type=11, cpp_type=10, label=1,
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
  serialized_start=891,
  serialized_end=954,
)

_ADDPROJECTQUOTARESPONSE.fields_by_name['result'].message_type = response__pb2._RESMES
_PROJECTQUOTARET.fields_by_name['project_quota_info_list'].message_type = _PROJECTQUOTAINFO
_LISTPROJECTQUOTARESPONSE.fields_by_name['result'].message_type = response__pb2._RESMES
_LISTPROJECTQUOTARESPONSE.fields_by_name['value'].message_type = _PROJECTQUOTARET
_DELETEPROJECTQUOTARESPONSE.fields_by_name['result'].message_type = response__pb2._RESMES
_UPDATEPROJECTQUOTARESPONSE.fields_by_name['result'].message_type = response__pb2._RESMES
DESCRIPTOR.message_types_by_name['AddProjectQuotaPara'] = _ADDPROJECTQUOTAPARA
DESCRIPTOR.message_types_by_name['AddProjectQuotaResponse'] = _ADDPROJECTQUOTARESPONSE
DESCRIPTOR.message_types_by_name['ListProjectQuotaPara'] = _LISTPROJECTQUOTAPARA
DESCRIPTOR.message_types_by_name['ProjectQuotaInfo'] = _PROJECTQUOTAINFO
DESCRIPTOR.message_types_by_name['ProjectQuotaRet'] = _PROJECTQUOTARET
DESCRIPTOR.message_types_by_name['ListProjectQuotaResponse'] = _LISTPROJECTQUOTARESPONSE
DESCRIPTOR.message_types_by_name['DeleteProjectQuotaPara'] = _DELETEPROJECTQUOTAPARA
DESCRIPTOR.message_types_by_name['DeleteProjectQuotaResponse'] = _DELETEPROJECTQUOTARESPONSE
DESCRIPTOR.message_types_by_name['UpdateProjectQuotaPara'] = _UPDATEPROJECTQUOTAPARA
DESCRIPTOR.message_types_by_name['UpdateProjectQuotaResponse'] = _UPDATEPROJECTQUOTARESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

AddProjectQuotaPara = _reflection.GeneratedProtocolMessageType('AddProjectQuotaPara', (_message.Message,), dict(
  DESCRIPTOR = _ADDPROJECTQUOTAPARA,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.AddProjectQuotaPara)
  ))
_sym_db.RegisterMessage(AddProjectQuotaPara)

AddProjectQuotaResponse = _reflection.GeneratedProtocolMessageType('AddProjectQuotaResponse', (_message.Message,), dict(
  DESCRIPTOR = _ADDPROJECTQUOTARESPONSE,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.AddProjectQuotaResponse)
  ))
_sym_db.RegisterMessage(AddProjectQuotaResponse)

ListProjectQuotaPara = _reflection.GeneratedProtocolMessageType('ListProjectQuotaPara', (_message.Message,), dict(
  DESCRIPTOR = _LISTPROJECTQUOTAPARA,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListProjectQuotaPara)
  ))
_sym_db.RegisterMessage(ListProjectQuotaPara)

ProjectQuotaInfo = _reflection.GeneratedProtocolMessageType('ProjectQuotaInfo', (_message.Message,), dict(
  DESCRIPTOR = _PROJECTQUOTAINFO,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ProjectQuotaInfo)
  ))
_sym_db.RegisterMessage(ProjectQuotaInfo)

ProjectQuotaRet = _reflection.GeneratedProtocolMessageType('ProjectQuotaRet', (_message.Message,), dict(
  DESCRIPTOR = _PROJECTQUOTARET,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ProjectQuotaRet)
  ))
_sym_db.RegisterMessage(ProjectQuotaRet)

ListProjectQuotaResponse = _reflection.GeneratedProtocolMessageType('ListProjectQuotaResponse', (_message.Message,), dict(
  DESCRIPTOR = _LISTPROJECTQUOTARESPONSE,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.ListProjectQuotaResponse)
  ))
_sym_db.RegisterMessage(ListProjectQuotaResponse)

DeleteProjectQuotaPara = _reflection.GeneratedProtocolMessageType('DeleteProjectQuotaPara', (_message.Message,), dict(
  DESCRIPTOR = _DELETEPROJECTQUOTAPARA,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.DeleteProjectQuotaPara)
  ))
_sym_db.RegisterMessage(DeleteProjectQuotaPara)

DeleteProjectQuotaResponse = _reflection.GeneratedProtocolMessageType('DeleteProjectQuotaResponse', (_message.Message,), dict(
  DESCRIPTOR = _DELETEPROJECTQUOTARESPONSE,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.DeleteProjectQuotaResponse)
  ))
_sym_db.RegisterMessage(DeleteProjectQuotaResponse)

UpdateProjectQuotaPara = _reflection.GeneratedProtocolMessageType('UpdateProjectQuotaPara', (_message.Message,), dict(
  DESCRIPTOR = _UPDATEPROJECTQUOTAPARA,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.UpdateProjectQuotaPara)
  ))
_sym_db.RegisterMessage(UpdateProjectQuotaPara)

UpdateProjectQuotaResponse = _reflection.GeneratedProtocolMessageType('UpdateProjectQuotaResponse', (_message.Message,), dict(
  DESCRIPTOR = _UPDATEPROJECTQUOTARESPONSE,
  __module__ = 'projectquota_pb2'
  # @@protoc_insertion_point(class_scope:YrcfAgent.UpdateProjectQuotaResponse)
  ))
_sym_db.RegisterMessage(UpdateProjectQuotaResponse)



_PROJECTQUOTA = _descriptor.ServiceDescriptor(
  name='ProjectQuota',
  full_name='YrcfAgent.ProjectQuota',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=957,
  serialized_end=1348,
  methods=[
  _descriptor.MethodDescriptor(
    name='AddProjectQuota',
    full_name='YrcfAgent.ProjectQuota.AddProjectQuota',
    index=0,
    containing_service=None,
    input_type=_ADDPROJECTQUOTAPARA,
    output_type=_ADDPROJECTQUOTARESPONSE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ListProjectQuota',
    full_name='YrcfAgent.ProjectQuota.ListProjectQuota',
    index=1,
    containing_service=None,
    input_type=_LISTPROJECTQUOTAPARA,
    output_type=_LISTPROJECTQUOTARESPONSE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='DeleteProjectQuota',
    full_name='YrcfAgent.ProjectQuota.DeleteProjectQuota',
    index=2,
    containing_service=None,
    input_type=_DELETEPROJECTQUOTAPARA,
    output_type=_DELETEPROJECTQUOTARESPONSE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='UpdateProjectQuota',
    full_name='YrcfAgent.ProjectQuota.UpdateProjectQuota',
    index=3,
    containing_service=None,
    input_type=_UPDATEPROJECTQUOTAPARA,
    output_type=_UPDATEPROJECTQUOTARESPONSE,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_PROJECTQUOTA)

DESCRIPTOR.services_by_name['ProjectQuota'] = _PROJECTQUOTA

# @@protoc_insertion_point(module_scope)
