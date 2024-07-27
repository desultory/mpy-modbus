from uasyncio import sleep_ms
from modbus_frame import ModbusFrame, FrameTooShortError
from rs485 import RS485, get_serial_chartime
from math import ceil
from utime import ticks_ms


class ModbusRTUClient:
    def __init__(self, address, tx_pin, rx_pin, de_pin, uart=0,
                 baudrate=19200, data_bits=8, parity=0, stop_bits=1,
                 debug=False):
        """
        address: int, device address
        tx_pin: int, pin number for UART TX
        rx_pin: int, pin number for UART RX
        de_pin: int, pin number for RS485 DE/RE
        uart: int, UART number
        baudrate: int, baudrate (default 19200)
        data_bits: int, number of data bits (default 8)
        parity: int, parity (None: no parity, 0: even, 1: odd)
        stop_bits: int, number of stop bits (default 1)
        """
        self.debug = debug
        if parity is None:
            stop_bits = 2  # Modbus RTU must use a 11-bit frame
        if baudrate < 19200:
            chartime = get_serial_chartime(baudrate, data_bits, parity, stop_bits)
            tx_delay = chartime * 3500  # Use the base char time for the tx_delay, convert to us
            chartime = chartime * 1.5  # Multiply by 1.5 to account for the 1.5 character time
        else:
            tx_delay = 1750  # 1750 us
            chartime = 0.750  # 750 us

        chartime = ceil(chartime)
        self.address = address
        self.serial = RS485(tx_pin, rx_pin, de_pin, uart,
                            baudrate, data_bits, parity, stop_bits,
                            tx_delay=tx_delay, timeout_char=chartime, poll_interval=chartime,
                            debug=debug)

        self.poll_interval = chartime * 2

        # Each key is a register address
        # Implied starting at 40001, so 0x0000 is 40001
        self.holding_registers = {}  # Each key is a register address

    def log(self, msg):
        if self.debug:
            print("[%d] %s" % (ticks_ms(), msg))

    async def runloop(self):
        print("Starting Modbus RTU Client")
        while True:
            for message in self.get_messages():
                await self.parse_recv(message)
            await sleep_ms(self.poll_interval)

    def get_messages(self):
        """ Get a message from message list """
        if self.serial.messages:
            yield self.serial.messages.pop(0)
        return None

    def parse_recv(self, data, i=0):
        """
        Try to parse a message from the receive buffer or the given data.
        If the data cannot be parsed, shift the buffer by one byte and try again.
        After 10 attempts, return.
        """
        if i > 10:
            return print("Failed to parse data after 10 attempts. Resetting buffer.")

        if not data:
            return print("No data to parse")

        try:
            await self.handle_frame(ModbusFrame.parse_frame(data))
        except ValueError as e:
            print("Failed to parse data: %s\n%s " % (e, data))
        except NotImplementedError as e:
            print("Failed to parse data: %s\n%s " % (e, data))
        except FrameTooShortError as e:
            print("Possible incomplete frame: %s\n%s " % (e, data))
            return

        data = data[1:]
        if data:
            return self.parse_recv(data, i + 1)

    async def handle_read_holding_registers(self, frame):
        """ Sends a response with the values of the requested registers """
        start = frame.data[0]
        if start > 49999:
            raise ValueError("Invalid register address: %s" % start)
        if start < 40001:
            start += 40000
        end = start + frame.data[1]
        register_data = b''
        for i in range(start, end):
            register_data += self.holding_registers.get(i, b'\x00\x00')
        response = ModbusFrame(address=self.address, function=3, data=register_data, response=1)
        await self.serial.send(response.to_bytes())

    async def handle_frame(self, frame):
        if frame.address == 0:
            print("Received broadcast frame: %s" % frame)
        elif frame.address != self.address:
            print("Received frame for another device: %s" % frame)
            return
        else:
            print("[%d] Received frame: %s" % (ticks_ms(), frame))
            if frame.function == 3:
                await self.handle_read_holding_registers(frame)



