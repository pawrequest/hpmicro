"""Laptop (CPython) side: typed command model -> DMX frame. Not deployed to the device."""

from dataclasses import dataclass

from shared import dmx_util

DMX_UNIVERSE_SIZE = 512


@dataclass(slots=True)
class DmxCommand:
    mode: int = 1
    level: float = 0.0  # 0..1
    r: int = 0
    g: int = 0
    b: int = 0

    def write_into(self, frame: bytearray, base: int = 0) -> None:
        """Write this command into `frame` at 0-based channel index `base`."""
        if base < 0 or base + dmx_util.FOOTPRINT > len(frame):
            raise ValueError(f'footprint does not fit at base {base}')
        frame[base + dmx_util.CH_MODE] = self.mode
        frame[base + dmx_util.CH_LEVEL] = dmx_util.encode_level(self.level)
        frame[base + dmx_util.CH_RED] = self.r
        frame[base + dmx_util.CH_GREEN] = self.g
        frame[base + dmx_util.CH_BLUE] = self.b

    def to_frame(self, base: int = 0) -> bytearray:
        frame = bytearray(DMX_UNIVERSE_SIZE)
        self.write_into(frame, base)
        return frame

    @classmethod
    def from_frame(cls, frame: bytes, base: int = 0) -> 'DmxCommand':
        return cls(
            mode=dmx_util.decode_mode(frame[base + dmx_util.CH_MODE]),
            level=dmx_util.decode_level(frame[base + dmx_util.CH_LEVEL]),
            r=frame[base + dmx_util.CH_RED],
            g=frame[base + dmx_util.CH_GREEN],
            b=frame[base + dmx_util.CH_BLUE],
        )
