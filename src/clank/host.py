"""Laptop (CPython) side: typed command model -> DMX frame. Not deployed to the device."""

from dataclasses import dataclass

from . import protocol as p

DMX_UNIVERSE_SIZE = 512


@dataclass(slots=True)
class Command:
    mode: int = p.MODE_STOP
    level: float = 0.0  # 0..1

    def write_into(self, frame: bytearray, base: int = 0) -> None:
        """Write this command into `frame` at 0-based channel index `base`."""
        if base < 0 or base + p.FOOTPRINT > len(frame):
            raise ValueError(f'footprint does not fit at base {base}')
        frame[base + p.CH_MODE] = self.mode
        frame[base + p.CH_LEVEL] = p.encode_level(self.level)

    def to_frame(self, base: int = 0) -> bytearray:
        frame = bytearray(DMX_UNIVERSE_SIZE)
        self.write_into(frame, base)
        return frame

    @classmethod
    def from_frame(cls, frame: bytes, base: int = 0) -> 'Command':
        return cls(
            mode=p.decode_mode(frame[base + p.CH_MODE]),
            level=p.decode_level(frame[base + p.CH_LEVEL]),
        )
