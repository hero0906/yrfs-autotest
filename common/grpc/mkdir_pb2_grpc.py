# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

#import mkdir_pb2 as mkdir__pb2
from . import mkdir_pb2 as mkdir__pb2


class MkDirStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.MkDir = channel.unary_unary(
        '/YrcfAgent.MkDir/MkDir',
        request_serializer=mkdir__pb2.MkDirRequest.SerializeToString,
        response_deserializer=mkdir__pb2.MkDirResponse.FromString,
        )


class MkDirServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def MkDir(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_MkDirServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'MkDir': grpc.unary_unary_rpc_method_handler(
          servicer.MkDir,
          request_deserializer=mkdir__pb2.MkDirRequest.FromString,
          response_serializer=mkdir__pb2.MkDirResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'YrcfAgent.MkDir', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))