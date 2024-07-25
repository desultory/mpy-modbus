from struct import pack


def generate_crc16_table():
    crc_table = []
    for byte in range(256):
        crc = 0x0000
        for _ in range(8):
            if (byte ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xa001
            else:
                crc >>= 1
            byte >>= 1
        crc_table.append(crc)
    return crc_table


CRC16_TABLE = generate_crc16_table()


def calculate_crc16(data):
    crc = 0xFFFF

    for char in data:
        crc = (crc >> 8) ^ CRC16_TABLE[((crc) ^ char) & 0xFF]

    return pack('<H', crc)
