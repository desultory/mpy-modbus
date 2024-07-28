class TextBuffer:
    def __init__(self, line_length, display_lines, max_length=2048):
        self.line_length = line_length
        self.display_lines = display_lines
        self.max_length = max_length
        self.clear()  # reset/initialize buffer

    def __add__(self, data):
        self.buffer.extend(data)
        if len(self.buffer) > self.max_length:
            self.buffer = self.buffer[-self.max_length:]
        self.updated = True
        return self

    @property
    def lines(self):
        if not self.updated:
            return self._lines

        lines = [[]]
        for char in self.buffer:
            # Create a new line if the current line is too long
            if len(lines[-1]) >= self.line_length:
                lines.append([])
            # Create a new line if the current character is a newline
            if char in [ord('\n'), ord('\r')]:
                lines.append([])
            elif char == 0:
                pass
            # Otherwise, add the character to the current line
            else:
                lines[-1].append(char)

            if len(lines) > 1 and lines[-2] == lines[-1]:
                from re import search
                if len(lines) > 2 and isinstance(lines[-3], str):
                    if match := search(r"^repeat<(\d+)>$", lines[-3]):
                        if match.group(1):
                            lines[-3] = f"repeat<{int(match.group(1)) + 1}>"
                            lines.pop()
                else:
                    lines[-2] = "repeat<2>"
        if lines[-1] == []:
            lines.pop()
        self._lines = lines
        self.updated = False
        return self._lines

    @property
    def pages(self):
        from math import ceil
        return ceil(len(self.lines) / self.display_lines)

    def get_page(self, page=0):
        start = page * self.display_lines
        end = start + self.display_lines
        return self.lines[start:end]

    @property
    def used(self):
        return int(sum(1 for char in self.buffer if char != 0) * 100 / len(self.buffer))

    def clear(self):
        self.buffer = bytearray(self.max_length)
        self._lines = [[]]
        self.updated = False

    def __str__(self):
        return self.buffer.decode('ascii')
