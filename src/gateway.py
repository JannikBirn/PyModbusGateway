import asyncio
import logging
from dataclasses import dataclass, field
from typing import cast

import pymodbus.client as modbusClient
import yaml
from pymodbus import FramerType
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.pdu import ModbusPDU
from pymodbus.server import ModbusTcpServer

from modbus.custom.CustomPassthrough import CustomPassthroughResponse, CustomPassthroughRequest, PassthroughPDUConfig

CONFIG_FILE_PATH = "../config.yml"

_logger = logging.getLogger(__file__)

@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 502
    slaves: list[int] = None

@dataclass
class ClientConfig:
    port: str = "/dev/ttyUSB0"
    retries: int = 0
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1

@dataclass
class Config:
    debug: bool = False
    server: ServerConfig = field(default_factory=ServerConfig)
    client: ClientConfig = field(default_factory=ClientConfig)
    passthroughs: list[PassthroughPDUConfig] = None


def load_config(path: str) -> Config:
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    # Convert nested dictionaries into proper dataclasses
    server_config = ServerConfig(**data.get('server', {}))
    client_config = ClientConfig(**data.get('client', {}))
    passthroughs = data.get('passthroughs', None)

    return Config(debug=data.get('debug', False),
                  server=server_config,
                  client=client_config,
                  passthroughs=passthroughs)

def setup_client(config: Config) -> modbusClient.ModbusSerialClient:
    _logger.info("Create client object")

    # Maybe use an async client (because it should be more performant)
    # Currently the RemoteSlaveContext has problems working with an async client
    client = modbusClient.ModbusSerialClient(
        port=config.client.port,
        retries=config.client.retries,
        baudrate=config.client.baudrate,
        bytesize=config.client.bytesize,
        parity=config.client.parity,
        stopbits=config.client.stopbits,
    )

    for passthrough in config.passthroughs:
        class_name = f"CustomReadRequest_{passthrough['functionCode']}"

        # Create a new dynamic class that inherits from ModbusPDU
        response = cast(type[ModbusPDU], type(class_name, (CustomPassthroughResponse,), {
            'function_code': passthrough['functionCode'],
            'rtu_byte_count_pos': passthrough['rtuByteCountPos'],
        }))
        client.register(response)
        _logger.info(f"Registered Response Function code: {passthrough['functionCode']}")

    return client

async def run_gateway(client: modbusClient.ModbusBaseSyncClient, config: Config):
    _logger.info("Starting Gateway")

    _logger.info("Starting Client")
    client.connect()
    _logger.info("Client connected")

    if config.server.slaves is None:
        raise Exception("There needs to be at least 1 slave configured.")

    store: dict | RemoteSlaveContext = {}
    for slave in config.server.slaves:
        store[slave] = RemoteSlaveContext(client, slave=slave)
    context = ModbusServerContext(slaves=store, single=False)

    custom_pdu: list[type[ModbusPDU]] = []

    for passthrough in config.passthroughs:
        class_name = f"CustomReadRequest_{passthrough['functionCode']}"

        # Create a new dynamic class that inherits from ModbusPDU
        request = cast(type[ModbusPDU], type(class_name, (CustomPassthroughRequest,), {
            'function_code': passthrough['functionCode'],
            'rtu_byte_count_pos': passthrough['rtuByteCountPos'],
        }))
        _logger.info(f"Added Request Function code: {passthrough['functionCode']}")
        custom_pdu.append(request)

    _logger.info("Starting server")
    await ModbusTcpServer(
        context=context,  # Data storage
        address=(config.server.host, config.server.port),  # listen address
        framer=FramerType.SOCKET,  # The framer strategy to use
        custom_pdu=custom_pdu
    ).serve_forever()

async def main():
    config = load_config(CONFIG_FILE_PATH)
    if config.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    client = setup_client(config)
    await run_gateway(client=client, config=config)

if __name__ == "__main__":
    asyncio.run(main())
