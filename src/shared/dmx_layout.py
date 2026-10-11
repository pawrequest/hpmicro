"""Declarative DMX channel layout, shared by laptop (CPython) and ESP32 (MicroPython).

A Layout is an ordered list of (name, kind). Offsets are assigned sequentially; each
kind knows how to turn raw bytes into a value and back, and what value to fall back
to on signal loss (`default`). Plain classes only: no typing/dataclasses/enum.

    LAYOUT = Layout([('mode', Enum((0, 100), 0)), ('speed', Signed()), ('r', U8())])
    LAYOUT.decode(frame, base, values)   # frame -> values (dict, updated in place)
    LAYOUT.encode(values, frame, base)   # values -> frame
"""


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
