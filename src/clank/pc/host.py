"""Laptop (CPython) side: layout-validated command -> DMX frame. Not deployed to the device."""

from shared.dmx_layout import Layout

DMX_UNIVERSE_SIZE = 512


class Command:
    """Mutable name->value mapping validated against a Layout.

    cmd = Command(LAYOUT, mode=MODE_RUN, r=255);  cmd['level'] = 0.5
    """

    def __init__(self, layout: Layout, **values):
        object.__setattr__(self, 'layout', layout)
        object.__setattr__(self, 'values', layout.defaults())
        self.update(**values)

    def update(self, **values) -> None:
        for name, v in values.items():
            self[name] = v

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value) -> None:
        if name not in self.layout.index:
            raise KeyError(name)
        self.values[name] = value

    def __getattr__(self, name):
        try:
            return self.values[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value) -> None:
        self[name] = value

    def __eq__(self, other) -> bool:
        return isinstance(other, Command) and self.layout is other.layout and self.values == other.values

    def write_into(self, frame: bytearray, base: int = 0) -> None:
        """Write into `frame` at 0-based channel index `base`."""
        self.layout.encode(self.values, frame, base)

    def to_frame(self, base: int = 0) -> bytearray:
        frame = bytearray(DMX_UNIVERSE_SIZE)
        self.write_into(frame, base)
        return frame

    @classmethod
    def from_frame(cls, layout: Layout, frame: bytes, base: int = 0) -> 'Command':
        cmd = cls(layout)
        layout.decode(frame, base, cmd.values)
        return cmd
