"""Declarative DMX channel layout, shared by laptop (CPython) and ESP32 (MicroPython).

A Layout is an ordered list of (name, kind). Offsets are assigned sequentially; each
kind knows how to turn raw bytes into a value and back, and what value to fall back
to on signal loss (`default`). Plain classes only: no typing/dataclasses/enum.

    LAYOUT = Layout([('mode', Enum((0, 100), 0)), ('speed', Signed()), ('r', U8())])
    LAYOUT.decode(frame, base, values)   # frame -> values (dict, updated in place)
    LAYOUT.encode(values, frame, base)   # values -> frame
"""


class U8:
    """Raw byte 0..255."""

    width = 1

    def __init__(self, default=0):
        self.default = default

    def decode(self, frame, i):
        return frame[i]

    def encode(self, value, frame, i):
        frame[i] = max(0, min(255, int(round(value))))


class Level(U8):
    """0..255 <-> 0.0..1.0."""

    def __init__(self, default=0.0):
        self.default = default

    def decode(self, frame, i):
        return frame[i] / 255

    def encode(self, value, frame, i):
        frame[i] = max(0, min(255, int(round(value * 255))))


class Signed(U8):
    """128 = 0.0, 1 = -1.0, 255 = +1.0 (e.g. speed). 0 is treated as -1.0 too."""

    def __init__(self, default=0.0):
        self.default = default

    def decode(self, frame, i):
        return max(-1.0, min(1.0, (frame[i] - 128) / 127))

    def encode(self, value, frame, i):
        frame[i] = max(0, min(255, int(round(value * 127)) + 128))


class Flag(U8):
    """Byte >= 128 -> True."""

    def __init__(self, default=False):
        self.default = default

    def decode(self, frame, i):
        return frame[i] >= 128

    def encode(self, value, frame, i):
        frame[i] = 255 if value else 0


class Enum(U8):
    """Exact byte match against `allowed`; anything else decodes to `default` (fail safe)."""

    def __init__(self, allowed, default):
        self.allowed = tuple(allowed)
        self.default = default

    def decode(self, frame, i):
        b = frame[i]
        return b if b in self.allowed else self.default

    def encode(self, value, frame, i):
        if value not in self.allowed:
            raise ValueError('value %r not allowed' % (value,))
        frame[i] = value


class Wide16(U8):
    """Coarse + fine byte pair, 0..65535 <-> 0.0..1.0."""

    width = 2

    def __init__(self, default=0.0):
        self.default = default

    def decode(self, frame, i):
        return ((frame[i] << 8) | frame[i + 1]) / 65535

    def encode(self, value, frame, i):
        n = max(0, min(65535, int(round(value * 65535))))
        frame[i] = n >> 8
        frame[i + 1] = n & 0xFF

