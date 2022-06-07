# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import license_pb2 as license__pb2


class LicenseStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetLicense = channel.unary_unary(
                '/YrcfAgent.License/GetLicense',
                request_serializer=license__pb2.GetLicensePara.SerializeToString,
                response_deserializer=license__pb2.GetLicenseResponse.FromString,
                )
        self.SetLicense = channel.unary_unary(
                '/YrcfAgent.License/SetLicense',
                request_serializer=license__pb2.SetLicensePara.SerializeToString,
                response_deserializer=license__pb2.SetLicenseResponse.FromString,
                )
        self.RequestLicense = channel.unary_unary(
                '/YrcfAgent.License/RequestLicense',
                request_serializer=license__pb2.RequestLicensePara.SerializeToString,
                response_deserializer=license__pb2.RequestLicenseResponse.FromString,
                )


class LicenseServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetLicense(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetLicense(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestLicense(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_LicenseServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetLicense': grpc.unary_unary_rpc_method_handler(
                    servicer.GetLicense,
                    request_deserializer=license__pb2.GetLicensePara.FromString,
                    response_serializer=license__pb2.GetLicenseResponse.SerializeToString,
            ),
            'SetLicense': grpc.unary_unary_rpc_method_handler(
                    servicer.SetLicense,
                    request_deserializer=license__pb2.SetLicensePara.FromString,
                    response_serializer=license__pb2.SetLicenseResponse.SerializeToString,
            ),
            'RequestLicense': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestLicense,
                    request_deserializer=license__pb2.RequestLicensePara.FromString,
                    response_serializer=license__pb2.RequestLicenseResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'YrcfAgent.License', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class License(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetLicense(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/YrcfAgent.License/GetLicense',
            license__pb2.GetLicensePara.SerializeToString,
            license__pb2.GetLicenseResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetLicense(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/YrcfAgent.License/SetLicense',
            license__pb2.SetLicensePara.SerializeToString,
            license__pb2.SetLicenseResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestLicense(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/YrcfAgent.License/RequestLicense',
            license__pb2.RequestLicensePara.SerializeToString,
            license__pb2.RequestLicenseResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
