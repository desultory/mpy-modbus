from machine import UART, Pin
from uasyncio import sleep_ms, create_task, Event, Lock
from utime import sleep_us, ticks_ms


class RS485:
    def __init__(self, tx_pin, rx_pin, de_pin, uart=0,
                 baudrate=9600, data_bits=8, parity=None, stop_bits=1,
                 timeout_char=2, poll_interval=100, tx_delay=0,
                 driver_delay=0.5, debug=False):
        self.debug = debug
        self.baudrate = baudrate
        self.driver_delay = driver_delay * timeout_char  # Number of char times to wait after sending data
        self.tx_delay = int(tx_delay)  # delay after sending data, in us
        if tx_delay > 0:
            timeout = int(tx_delay / 1000 + timeout_char)  # timeout for uart read, in ms
        else:
            timeout = timeout_char * 2  # Otherwise, wait for 2 char times
        self.uart = UART(uart, baudrate=baudrate, tx=tx_pin, rx=rx_pin, bits=data_bits,
                         parity=parity, stop=stop_bits, timeout_char=timeout_char, timeout=timeout)
        self.log(f"Initialized UART: {self.uart}")
        self.de = Pin(de_pin, mode=Pin.OUT)

        self.poll_interval = int(poll_interval)  # 0 to poll continuously
        self.messages = []

        self.run = Event()
        self.dev_lock = Lock()
        self.task = create_task(self.runloop())

    def log(self, msg):
        if self.debug:
            print("[%d] %s" % (ticks_ms(), msg))

    async def runloop(self):
        self.run.set()
        while True:
            await self.run.wait()
            await self.recv()
            if self.poll_interval:
                await sleep_ms(self.poll_interval)

    async def recv(self):
        async with self.dev_lock:
            self.de.off()  # Set DE pin to receive mode
            self._recv()  # Get some data

    def _recv(self):
        if data := self.uart.read():
            self.log(f"Received data: {data.hex()}")
            self.messages.append(data)

    def _send(self, data):
        self.de.on()
        self.log(f"Sending data: {data.hex()}")
        self.uart.write(data)
        self.uart.flush()
        sleep_us(int(self.driver_delay * 1000))  # Wait for the rs485 driver to complete the transmission
        self.de.off()  # Only disable DE after the uart write is complete

    async def send(self, data):
        async with self.dev_lock:
            self._send(data)
            sleep_us(self.tx_delay)  # Sleep between consecutive transmissions

