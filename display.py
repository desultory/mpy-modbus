from ssd1306 import SSD1306_I2C
from asyncio import sleep_ms

from text_buffer import TextBuffer


class Display:
    MODES = ['text', 'info']

    def __init__(self, i2c, display_x=128, display_y=64, display_mode='text',
                 flip=False,
                 left_button=10, down_button=11, up_button=12, right_button=13):
        self.display_x = display_x
        self.display_y = display_y
        self.line_length = display_x // 8
        self.display_lines = display_y // 8
        self.display_chars = self.line_length * self.display_lines

        self.flip = flip
        self.display = SSD1306_I2C(display_x, display_y, i2c)
        self.text_lines = TextBuffer(line_length=self.line_length, display_lines=self.display_lines)

    async def start(self):
        print("Starting display.")
        self.display.fill(0)
        self.text_lines += 'Starting...\n'
        self.display.show()

    async def runloop(self):
        await self.start()
        while True:
            await sleep_ms(1000)
            await self.display_text()
            self.display.show()

    async def display_text(self):
        self.display.fill(0)
        display_text = self.text_lines.get_page(0)
        for line_number, line in enumerate(display_text):
            await self.set_line(line_number, line)

    async def set_line(self, line_number, text):
        for char_number, char in enumerate(text):
            text_char = chr(char) if isinstance(char, int) else char
            self.display.text(text_char, char_number * 8, line_number * 8)


