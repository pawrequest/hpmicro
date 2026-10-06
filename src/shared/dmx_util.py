"""Shared DMX channel map. Single source of truth for laptop (CPython) and ESP32 (MicroPython).

Must stay runtime-portable: plain constants and pure functions only. No typing,
dataclasses, enum or hardware imports. Copy/freeze this file onto the device.

Channel table (offsets relative to the device's DMX start address):

    offset  name      encoding
    0       CH_MODE   MODE_* value
    1       CH_LEVEL  0..255 -> 0.0..1.0

PLACEHOLDER content: replace channels as the real design firms up.
"""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


PROTOCOL_VERSION = const(1)

# Channel offsets
CH_MODE = const(0)
CH_LEVEL = const(1)
FOOTPRINT = const(2)  # number of channels used

# CH_MODE values (spaced apart so small DMX jitter can't flip a mode)
MODE_STOP = const(0)
MODE_RUN = const(100)


def encode_level(frac):
    """0.0..1.0 -> 0..255 (clamped)."""
    return max(0, min(255, round(frac * 255)))


def decode_level(byte):
    return byte / 255


def decode_mode(byte):
    """Map a raw byte to a MODE_* constant; unknown values fail safe to MODE_STOP."""
    return MODE_RUN if byte == MODE_RUN else MODE_STOP
