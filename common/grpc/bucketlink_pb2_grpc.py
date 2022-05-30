# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import bucketlink_pb2 as bucketlink__pb2


class BucketLinkStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.ListBucketLinks = channel.unary_stream(
        '/YrcfAgent.BucketLink/ListBucketLinks',
        request_serializer=bucketlink__pb2.ListBucketLinksRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.ListBucketLinksResponse.FromString,
        )
    self.AddBucketLink = channel.unary_unary(
        '/YrcfAgent.BucketLink/AddBucketLink',
        request_serializer=bucketlink__pb2.AddBucketLinkRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.AddBucketLinkResponse.FromString,
        )
    self.DelBucketLink = channel.unary_unary(
        '/YrcfAgent.BucketLink/DelBucketLink',
        request_serializer=bucketlink__pb2.DelBucketLinkRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.DelBucketLinkResponse.FromString,
        )
    self.ImportBucketLink = channel.unary_unary(
        '/YrcfAgent.BucketLink/ImportBucketLink',
        request_serializer=bucketlink__pb2.ImportBucketLinkRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.ImportBucketLinkResponse.FromString,
        )
    self.ExportBucketLink = channel.unary_unary(
        '/YrcfAgent.BucketLink/ExportBucketLink',
        request_serializer=bucketlink__pb2.ExportBucketLinkRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.ExportBucketLinkResponse.FromString,
        )
    self.StatBucketLink = channel.unary_stream(
        '/YrcfAgent.BucketLink/StatBucketLink',
        request_serializer=bucketlink__pb2.StatBucketLinkRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.StatBucketLinkResponse.FromString,
        )
    self.BucketLinkSubscribeOps = channel.unary_unary(
        '/YrcfAgent.BucketLink/BucketLinkSubscribeOps',
        request_serializer=bucketlink__pb2.BucketLinkSubscribeOpsRequest.SerializeToString,
        response_deserializer=bucketlink__pb2.BucketLinkSubscribeOpsResponse.FromString,
        )


class BucketLinkServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def ListBucketLinks(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def AddBucketLink(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def DelBucketLink(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ImportBucketLink(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ExportBucketLink(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def StatBucketLink(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def BucketLinkSubscribeOps(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_BucketLinkServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'ListBucketLinks': grpc.unary_stream_rpc_method_handler(
          servicer.ListBucketLinks,
          request_deserializer=bucketlink__pb2.ListBucketLinksRequest.FromString,
          response_serializer=bucketlink__pb2.ListBucketLinksResponse.SerializeToString,
      ),
      'AddBucketLink': grpc.unary_unary_rpc_method_handler(
          servicer.AddBucketLink,
          request_deserializer=bucketlink__pb2.AddBucketLinkRequest.FromString,
          response_serializer=bucketlink__pb2.AddBucketLinkResponse.SerializeToString,
      ),
      'DelBucketLink': grpc.unary_unary_rpc_method_handler(
          servicer.DelBucketLink,
          request_deserializer=bucketlink__pb2.DelBucketLinkRequest.FromString,
          response_serializer=bucketlink__pb2.DelBucketLinkResponse.SerializeToString,
      ),
      'ImportBucketLink': grpc.unary_unary_rpc_method_handler(
          servicer.ImportBucketLink,
          request_deserializer=bucketlink__pb2.ImportBucketLinkRequest.FromString,
          response_serializer=bucketlink__pb2.ImportBucketLinkResponse.SerializeToString,
      ),
      'ExportBucketLink': grpc.unary_unary_rpc_method_handler(
          servicer.ExportBucketLink,
          request_deserializer=bucketlink__pb2.ExportBucketLinkRequest.FromString,
          response_serializer=bucketlink__pb2.ExportBucketLinkResponse.SerializeToString,
      ),
      'StatBucketLink': grpc.unary_stream_rpc_method_handler(
          servicer.StatBucketLink,
          request_deserializer=bucketlink__pb2.StatBucketLinkRequest.FromString,
          response_serializer=bucketlink__pb2.StatBucketLinkResponse.SerializeToString,
      ),
      'BucketLinkSubscribeOps': grpc.unary_unary_rpc_method_handler(
          servicer.BucketLinkSubscribeOps,
          request_deserializer=bucketlink__pb2.BucketLinkSubscribeOpsRequest.FromString,
          response_serializer=bucketlink__pb2.BucketLinkSubscribeOpsResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'YrcfAgent.BucketLink', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))