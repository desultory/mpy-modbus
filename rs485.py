from machine import UART, Pin
from ring_bytes import RingBytes
from uasyncio import sleep_ms, create_task, Event, Lock
from utime import sleep_us, ticks_us, ticks_diff


class RS485:
    def __init__(self, tx_pin, rx_pin, de_pin, uart=0,
                 baudrate=9600, data_bits=8, parity=None,
                 stop_bits=1, poll_interval=100, tx_delay=0):
        self.baudrate = baudrate
        self.uart = UART(uart, baudrate=baudrate, tx=tx_pin, rx=rx_pin, bits=data_bits, parity=parity, stop=stop_bits)
        self.de = Pin(de_pin, mode=Pin.OUT)

        self.poll_interval = int(poll_interval)
        self.sleep_us = int((tx_delay - int(tx_delay)) * 1000)
        self.tx_delay = int(tx_delay)
        self.character_timeout = int((data_bits + 1 + stop_bits) * 1000 * 1000 / baudrate * 1.5)
        self.receive_buffer = RingBytes(1024)

        self.run = Event()
        self.dev_lock = Lock()
        self.task = create_task(self.runloop())

    async def runloop(self):
        self.run.set()
        while True:
            await self.run.wait()
            await self.recv()
            await sleep_ms(self.poll_interval)
            if self.sleep_us:
                sleep_us(self.sleep_us * 2)

    async def recv(self):
        async with self.dev_lock:
            self.de.off()  # Set DE pin to receive mode
            if self.uart.any():
                received = ticks_us()
                while ticks_diff(ticks_us(), received) < self.character_timeout:
                    self._recv()  # Get some data

    def _recv(self):
        if len := self.uart.any():
            self.receive_buffer += self.uart.read(len)

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
            await sleep_ms(self.tx_delay)
            if self.sleep_us:
                sleep_us(self.sleep_us)
            self.de.off()

