from machine import UART, Pin
from uasyncio import sleep_ms, create_task, Event, Lock
from utime import sleep_us


class RS485:
    def __init__(self, tx_pin, rx_pin, de_pin, uart=0,
                 baudrate=9600, data_bits=8, parity=None, stop_bits=1,
                 timeout_char=2, poll_interval=100, tx_delay=0):
        self.baudrate = baudrate
        self.tx_delay = int(tx_delay)  # delay after sending data, in us
        timeout = int(tx_delay / 1000 + timeout_char)  # timeout for uart read, in ms
        self.uart = UART(uart, baudrate=baudrate, tx=tx_pin, rx=rx_pin, bits=data_bits,
                         parity=parity, stop=stop_bits, timeout_char=timeout_char, timeout=timeout)
        print("Initialized UART:", self.uart)
        self.de = Pin(de_pin, mode=Pin.OUT)

        self.poll_interval = int(poll_interval)
        self.messages = []

        self.run = Event()
        self.dev_lock = Lock()
        self.task = create_task(self.runloop())

    async def runloop(self):
        self.run.set()
        while True:
            await self.run.wait()
            await self.recv()
            await sleep_ms(self.poll_interval)

    async def recv(self):
        async with self.dev_lock:
            self.de.off()  # Set DE pin to receive mode
            self._recv()  # Get some data

    def _recv(self):
        if data := self.uart.read():
            print("Received:", data)
            self.messages.append(data)

    def _send(self, data):
        """
        Send wrapper.
        doesn't return the DE pin to receive mode, as timing is handled by async
        """
        self.de.on()
        self.uart.write(data)
        self.uart.flush()

    async def send(self, data):
        async with self.dev_lock:
            self._send(data)
            sleep_us(self.tx_delay)
            self.de.off()

