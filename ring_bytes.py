class RingBytes(bytearray):
    """ A bytearray that has a maximum length and acts like a ring buffer. """
    def __init__(self, max_length):
        """ Init using super, then clear the buffer. """
        self.max_length = max_length
        super().__init__()

    def extend(self, item):
        super().extend(item)
        if len(self) > self.max_length:
            self = self[-self.max_length:]

    def clear(self):
        self[:] = RingBytes(self.max_length)

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __str__(self):
        try:
            return self.lstrip(b'\x00').decode()
        except UnicodeError:
            return self.lstrip(b'\x00')

