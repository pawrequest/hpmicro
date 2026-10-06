"""Run on desktop: python -m pytest src/clank (or python -m unittest)."""

import time
import unittest

from shared import dmx_util as p
from clank.esp import dmx_state
from clank.pc.host import DmxCommand


class RoundTrip(unittest.TestCase):
    def test_roundtrip_with_offset(self):
        cmd = DmxCommand(mode=p.MODE_RUN, level=1.0)
        frame = cmd.to_frame(base=9)
        self.assertEqual(frame[9 + p.CH_MODE], p.MODE_RUN)
        self.assertEqual(frame[9 + p.CH_LEVEL], 255)
        self.assertEqual(DmxCommand.from_frame(frame, base=9), cmd)

    def test_unknown_mode_fails_safe(self):
        self.assertEqual(p.decode_mode(101), p.MODE_STOP)

    def test_level_clamped(self):
        self.assertEqual(p.encode_level(2.0), 255)
        self.assertEqual(p.encode_level(-1.0), 0)

    def test_footprint_must_fit(self):
        with self.assertRaises(ValueError):
            DmxCommand().write_into(bytearray(1))


class DeviceState(unittest.TestCase):
    def setUp(self):
        # desktop shims for MicroPython's tick functions
        time.ticks_ms = lambda: int(time.monotonic() * 1000)
        time.ticks_diff = lambda a, b: a - b

    def test_update_and_timeout(self):
        s = dmx_state.DmxState()
        s.update(DmxCommand(p.MODE_RUN, 1.0).to_frame())
        self.assertTrue(s.valid)
        self.assertEqual(s.mode, p.MODE_RUN)
        s._last_ms -= dmx_state.SIGNAL_TIMEOUT_MS + 1
        s.check_timeout()
        self.assertFalse(s.valid)
        self.assertEqual(s.mode, p.MODE_STOP)


if __name__ == '__main__':
    unittest.main()
