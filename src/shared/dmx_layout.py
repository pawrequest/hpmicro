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


class Layout:
    def __init__(self, channels):
        self.names = tuple(n for n, _ in channels)
        self._kinds = tuple(k for _, k in channels)
        offsets = []
        pos = 0
        for k in self._kinds:
            offsets.append(pos)
            pos += k.width
        self._offsets = tuple(offsets)
        self.footprint = pos
        self.index = {n: j for j, n in enumerate(self.names)}

    def defaults(self):
        return {n: k.default for n, k in zip(self.names, self._kinds)}

    def offset(self, name):
        return self._offsets[self.index[name]]

    def decode(self, frame, base=0, values=None):
        """Decode `frame` at 0-based `base` into `values` (new dict if None); returns it."""
        if values is None:
            values = {}
        for n, k, o in zip(self.names, self._kinds, self._offsets):
            values[n] = k.decode(frame, base + o)
        return values

    def encode(self, values, frame, base=0):
        """Write `values` (missing names use defaults) into `frame`."""
        if base < 0 or base + self.footprint > len(frame):
            raise ValueError('footprint does not fit at base %d' % base)
        for n, k, o in zip(self.names, self._kinds, self._offsets):
            k.encode(values[n] if n in values else k.default, frame, base + o)
