from uasyncio import run
from modbus_rtu import ModbusRTUClient

client = ModbusRTUClient(1, 12, 13, 11, baudrate=921600, debug=True)

run(client.runloop())

