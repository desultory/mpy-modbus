from uasyncio import run
from modbus_rtu import ModbusRTUClient

client = ModbusRTUClient(2, 12, 13, 11)


run(client.runloop())

