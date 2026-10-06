"""ESP32 (MicroPython) side: lean frame decoder with signal-loss failsafe.

No dataclasses/typing at runtime. Hardware access stays out of here: the
application reads `state` and acts, keeping this module testable on a desktop.
"""

import time

try:
    from shared import dmx_util as p
except (ImportError, ValueError):
    import protocol as p  # flat layout on the device

SIGNAL_TIMEOUT_MS = 500


class DmxState:
    __slots__ = ('mode', 'level', 'valid', '_last_ms')

    def __init__(self):
        self.mode = p.MODE_STOP
        self.level = 0.0
        self.valid = False  # False => no recent frame; act as stopped
        self._last_ms = 0

    def update(self, frame, base=0):
        """Decode `frame` (bytes-like) in place; no allocation beyond float boxing."""
        self.mode = p.decode_mode(frame[base + p.CH_MODE])
        self.level = p.decode_level(frame[base + p.CH_LEVEL])
        self.valid = True
        self._last_ms = time.ticks_ms()

    def check_timeout(self):
        """Call periodically; drops to failsafe if frames stopped arriving."""
        if self.valid and time.ticks_diff(time.ticks_ms(), self._last_ms) > SIGNAL_TIMEOUT_MS:
            self.valid = False
            self.mode = p.MODE_STOP
            self.level = 0.0
