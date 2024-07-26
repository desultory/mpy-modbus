from uasyncio import sleep_ms
from modbus_frame import ModbusFrame, FrameTooShortError, get_serial_chartime
from rs485 import RS485


class ModbusRTUClient:
    def __init__(self, address, tx_pin, rx_pin, de_pin, uart=0,
                 baudrate=9600, data_bits=8, parity=None, stop_bits=1):
        chartime = get_serial_chartime(baudrate, data_bits, stop_bits)
        tx_delay = chartime * 3.5
        self.address = address
        self.serial = RS485(tx_pin, rx_pin, de_pin, uart,
                            baudrate, data_bits, parity, stop_bits,
                            tx_delay=tx_delay, poll_interval=tx_delay * 2)

    async def runloop(self):
        print("Starting Modbus RTU Client")
        while True:
            if frame := self.parse_recv():
                if frame.address == self.address:
                    print("Received frame: %s" % frame)
                else:
                    print("Received frame for another device: %s" % frame)

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
        except FrameTooShortError as e:
            print("Possible incomplete frame: %s\n%s " % (e, data))
            self.serial.receive_buffer = data
            return

        if data:
            return self.parse_recv(data)
        self.serial.receive_buffer = data
