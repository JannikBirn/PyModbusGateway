# PyModbusGateway
PyModbusGateway is open-source Modbus TCP to Modbus RTU (RS-232/485) gateway. It presents a network of RTU slaves as single TCP slave.

That is a TCP-Slave (or server) which acts as a RTU-master to get data from Modbus RTU-slave devices.

This project uses [pymodbus](https://github.com/pymodbus-dev/pymodbus) for the modbus server and client.

## Supported function codes:
- 01: Read coil status
- 02: Read input status
- 03: Read holding registers
- 04: Read input registers
- 05: Force single coil
- 06: Preset single register
- 07: Read exception status
- 15: Force multiple coils
- 16: Preset multiple registers

Custom function codes can be configured as "passthrough".

### Passthrough functions:
Passthrough functions can be used to pass custom function codes between the RTU and TCP connection.
These can be configured in the `config.yml` file.

Example:
```yaml
passthroughs:
  - functionCode: 0x41
    rtuByteCountPos: 3
```

This means that all custom functions with the code ``0x41`` will be passed through this Gateway.
To pass the functions the gateway needs to know the length of the message, this is done by providing the byte that contains the length of the message, in this example it is the 3rd byte.

This example will work with the Huawei [Solar Inverter Modbus Interface Definitions](https://github.com/wlcrs/huawei_solar/files/10920652/Solar.Inverter.Modbus.Interface.Definitions.v05.pdf) in section 6.3.7 the custom function 0x41 is defined.

## Usage
This project is ment to be used as a docker container.

### config.yml

To configure this project a `config.yml` file is used.

Example:
````yaml
debug: False #Show debug logs

server:
  host: "" #Server host, no value = localhost
  port: 502 #TCP Server port
  slaves: [1, 2] #The RTU Slaves addresses that should be forward

client:
  port: "/dev/ttyUSB0" #The usb device 
  retries: 0 #The number of retries
  #Modbus RTU configuration
  baudrate: 9600
  bytesize: 8
  parity: "N"
  stopbits: 1

#Array of passthroughs functions
passthroughs:
  - functionCode: 0x41
    rtuByteCountPos: 3
````

### Docker

``compose.yml``
````yaml
services:
  modbus-gateway:
    image: jannli/py-modbus-gateway:x.x.x #Replace x.x.x with the latest release version
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
#    privileged: true #Only necessary if u want to use host port 502
    ports:
      - '1502:502/tcp'
    volumes:
      - <path>/config.yml:/config.yml
````

# Inspiration
[3cky/mbusd](https://github.com/3cky/mbusd)