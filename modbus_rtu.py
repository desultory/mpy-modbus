from uasyncio import sleep_ms
from modbus_frame import ModbusFrame
from rs485 import RS485


class ModbusRTUClient:
    def __init__(self, address, tx_pin, rx_pin, de_pin, uart=0, baudrate=9600):
        self.address = address
        self.serial = RS485(tx_pin, rx_pin, de_pin, uart, baudrate)

    async def runloop(self):
        print("Starting Modbus RTU Client")
        while True:
            self.parse_recv()
            await sleep_ms(1000)

    def parse_recv(self, data=None):
        data = data or self.serial.receive_buffer
        if not data:
            print("No data to parse")
            return

        try:
            frame, new_recv = ModbusFrame.parse_frame(data)
            self.serial.receive_buffer = new_recv
            return frame
        except ValueError as e:
            print("Failed to parse data: %s\n%s " % (e, data))
            data = data[1:]
        except NotImplementedError as e:
            print("Failed to parse data: %s\n%s " % (e, data))
            data = data[1:]

        if data:
            self.parse_recv(data)
