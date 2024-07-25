from machine import UART, Pin
from ring_bytes import RingBytes
from uasyncio import sleep_ms, create_task, Event, Lock


class RS485:
    def __init__(self, tx_pin, rx_pin, de_pin, uart=0, baudrate=9600, poll_interval=100):
        self.baudrate = baudrate
        self.uart = UART(uart, baudrate=baudrate, tx=tx_pin, rx=rx_pin)
        self.de = Pin(de_pin, mode=Pin.OUT)

        self.poll_interval = poll_interval
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

    async def recv(self):
        async with self.dev_lock:
            self._recv()

    def _recv(self):
        self.de.off()
        if len := self.uart.any():
            self.receive_buffer += self.uart.read(len)

    def _send(self, data):
        self.de.on()
        self.uart.write(data)

    async def _slow_send(self, data):
        """ Wait a bit after sending to ensure data is sent before disabling DE """
        self._send(data)
        await sleep_ms(len(data) * self.baudrate // 4000)

    async def send(self, data):
        async with self.dev_lock:
            await self._slow_send(data)


