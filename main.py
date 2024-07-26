from uasyncio import run
from modbus_rtu import ModbusRTUClient

client = ModbusRTUClient(1, 12, 13, 11)


run(client.runloop())

