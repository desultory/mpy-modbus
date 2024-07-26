from crc16_modbus import calculate_crc16
from struct import pack, unpack


FUNCTION_CODES = {1: ('HH', "read_coils"),
                  2: "Read Discrete Inputs",
                  3: ('HH', "read_holding_registers"),
                  4: "Read Input Registers",
                  5: "Write Single Coil",
                  6: "Write Single Register",
                  15: "Write Multiple Coils",
                  16: "Write Multiple Registers"}


def get_serial_chartime(baudrate, data_bits, parity, stop_bits):
    """ Returns the time it takes to send a single byte over serial """
    packet_size = data_bits + stop_bits + (1 if parity is not None else 0)
    packets_per_second = baudrate / packet_size
    chartime_ms = 1000 / packets_per_second
    return chartime_ms


class FrameTooShortError(Exception):
    pass


class ModbusFrame:
    @staticmethod
    def parse_frame(frame_bytes):
        """ Attempts to parse a modbus frame from a bytearray """
        print("Parsing bytes: ", frame_bytes.hex())
        if len(frame_bytes) < 6:
            raise FrameTooShortError("Frame too short: %d" % len(frame_bytes))
        address, function = unpack(">BB", frame_bytes[:2])

        if address > 247:
            raise ValueError("Invalid address: %d" % address)

        if function not in FUNCTION_CODES:
            raise ValueError("Function code not supported: %d" % function)

        try:
            func = getattr(ModbusFrame, FUNCTION_CODES[function][1])
        except AttributeError:
            raise NotImplementedError("Function not implemented: %s" % FUNCTION_CODES[function][1])
        params = FUNCTION_CODES[function][0]

        frame = func(address, *unpack(">" + params, frame_bytes[len(params):]))
        data_crc = frame_bytes[len(frame.pdu):len(frame.pdu) + 2]
        if data_crc != frame.crc:
            raise ValueError("CRC mismatch: %s != %s" % (data_crc, frame.crc))

        return frame, frame_bytes[len(frame.to_bytes()):]

    def __init__(self, address, function, data, response=False):
        if function not in FUNCTION_CODES:
            raise ValueError("Function code not supported: %d" % function)

        self.address = address
        self.function = function
        if isinstance(data, tuple):
            if len(data) != len(FUNCTION_CODES[function][0]):
                raise ValueError("Invalid data length: %d != %d" %
                                 (len(data), len(FUNCTION_CODES[function][0])))
        elif response:
            if len(data) < 1 or len(data) > 253:
                raise ValueError("Invalid data length: %d" % len(data))
        self.data = data
        self.response = response

    def __str__(self):
        return f"Address: {self.address}, Function: {FUNCTION_CODES[self.function][1]}, Data: {self.data}"

    def to_bytes(self):
        return self.pdu + self.crc

    def __repr__(self):
        return f"ModbusFrame({self.address}, {self.function}, {self.data})"

    @property
    def pdu(self):
        if self.response:
            data_length = len(self.data)
            data_format = "B" * data_length
            return pack(">BBB" + data_format, self.address, self.function, data_length, *self.data)
        else:
            function_format = FUNCTION_CODES[self.function][0]
            return pack(">BB" + function_format, self.address, self.function, *self.data)

    @property
    def crc(self):
        return calculate_crc16(self.pdu)

    @staticmethod
    def read_coils(address, start, count):
        return ModbusFrame(address, 1, (start, count))

    @staticmethod
    def read_holding_registers(address, start, count):
        return ModbusFrame(address, 3, (start, count))

