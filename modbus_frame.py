from crc16_modbus import calculate_crc16
from struct import pack, unpack


FUNCTION_CODES = {1: ('HH', "Read Coils"),
                  2: "Read Discrete Inputs",
                  3: ('HH', "Read Holding Registers"),
                  4: "Read Input Registers",
                  5: "Write Single Coil",
                  6: "Write Single Register",
                  15: "Write Multiple Coils",
                  16: "Write Multiple Registers"}


def get_serial_chartime(baudrate, data_bits, stop_bits):
    """ Returns the time it takes to send a single byte over serial """
    packet_size = data_bits + stop_bits + 1
    packets_per_second = baudrate / packet_size
    chartime_ms = 1000 / packets_per_second
    return chartime_ms


class FrameTooShortError(Exception):
    pass


class ModbusFrame:
    @staticmethod
    def parse_frame(frame_bytes):
        """ Attempts to parse a modbus frame from a bytearray """
        print("Parsing bytes: ", frame_bytes)
        if len(frame_bytes) < 6:
            raise FrameTooShortError("Frame too short: %d" % len(frame_bytes))
        address, function = unpack(">BB", frame_bytes[:2])

        if address > 247:
            raise ValueError("Invalid address: %d" % address)

        if function not in FUNCTION_CODES:
            raise ValueError("Function code not supported: %d" % function)

        if function == 1 or function == 3:
            frame = ModbusFrame.read_coil(address, *unpack(">HH", frame_bytes[2:]))
            data_crc = frame_bytes[6:8]
            if data_crc != calculate_crc16(frame.pdu):
                raise ValueError("CRC mismatch: %s != %s" % (data_crc, calculate_crc16(frame.pdu)))
        else:
            raise NotImplementedError("Function not implemented: %d" % function)

        return frame, frame_bytes[len(frame.to_bytes()):]

    def __init__(self, address, function, data):
        if function not in FUNCTION_CODES:
            raise ValueError("Function code not supported: %d" % function)

        self.address = address
        self.function = function
        self.data = data

    def __str__(self):
        return f"Address: {self.address}, Function: {FUNCTION_CODES[self.function][1]}, Data: {self.data}"

    def to_bytes(self):
        return self.pdu + self.crc

    def __repr__(self):
        return f"ModbusFrame({self.address}, {self.function}, {self.data})"

    @property
    def pdu(self):
        function_format = FUNCTION_CODES[self.function][0]
        if self.function != 1:
            data_format = 'B' * len(self.data)
            return pack(">B" + function_format + data_format,
                        self.address, self.function, *self.data)
        return pack(">BB" + function_format, self.address, self.function, *self.data)

    @property
    def crc(self):
        return calculate_crc16(self.pdu)

    @staticmethod
    def read_coil(address, start, count):
        return ModbusFrame(address, 1, (start, count))

    @staticmethod
    def read_holding_registers(address, start, count):
        return ModbusFrame(address, 3, (start, count))

