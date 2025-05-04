import logging
from dataclasses import dataclass
from typing import cast

from pymodbus import ExceptionResponse
from pymodbus.client import ModbusBaseSyncClient
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.pdu import ModbusPDU

_logger = logging.getLogger(__file__)

@dataclass
class PassthroughPDUConfig:
    functionCode: int = None
    rtuByteCountPos: int = None

class CustomPassthroughRequest(ModbusPDU):

    def __init__(self, raw_data=b"", **kwargs):
        ModbusPDU.__init__(self, **kwargs)
        self.raw_data = raw_data  # Everything after function code

    def encode(self):
        _logger.debug(f"[CustomPassthroughRequest] encode data: {self.raw_data}")
        return self.raw_data

    def decode(self, data):
        _logger.debug(f"[CustomPassthroughRequest] decode data: {data}")
        self.raw_data = data

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        _logger.debug(f"[CustomPassthroughRequest] update_datastore data: {self.raw_data}, context:{context}")
        if isinstance(context, RemoteSlaveContext):
            remoteSlaveContext : RemoteSlaveContext = context
            if isinstance(remoteSlaveContext._client, ModbusBaseSyncClient):
                client : ModbusBaseSyncClient = remoteSlaveContext._client
                response = cast(CustomPassthroughResponse, client.execute(no_response_expected=False, request=self))
                _logger.debug(f"[CustomPassthroughRequest] update_datastore response: {response}")
                return response
        return ExceptionResponse(0, 0)

class CustomPassthroughResponse(ModbusPDU):

    def __init__(self, raw_data=b"", **kwargs):
        ModbusPDU.__init__(self, **kwargs)
        self.raw_data = raw_data

    def encode(self):
        _logger.debug(f"[CustomPassthroughResponse] encode data: {self.raw_data}")
        return self.raw_data

    def decode(self, data):
        _logger.debug(f"[CustomPassthroughResponse] decode data: {data}")
        self.raw_data = data
