from uasyncio import run, create_task
from modbus_rtu import ModbusRTUClient
from display import Display
from machine import I2C, Pin
from utime import sleep_ms

display_i2c = I2C(0, scl=Pin(5), sda=Pin(4))

try:
    display = Display(display_i2c)
    create_task(display.runloop())
    display.text_lines += "MB RTU client\n"
except Exception as e:
    print(e)
    display = None
    sleep_ms(500)


client = ModbusRTUClient(1, 12, 13, 11, baudrate=921600, debug=True, display_lines=display.text_lines)


run(client.runloop())

