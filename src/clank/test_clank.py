"""Run on desktop from src: python -m unittest clank.test_clank"""

import time
import unittest

from shared import dmx_util as p
from shared.dmx_layout import Enum, Flag, Layout, Level, Signed, U8, Wide16
from clank.esp.dmx_device import SIGNAL_TIMEOUT_MS, DmxDevice
from clank.pc.host import Command


class Kinds(unittest.TestCase):
    def roundtrip(self, kind, value):
        frame = bytearray(4)
        kind.encode(value, frame, 1)
        return kind.decode(frame, 1)

    def test_roundtrips(self):
        self.assertEqual(self.roundtrip(U8(), 200), 200)
        self.assertEqual(self.roundtrip(Level(), 1.0), 1.0)
        self.assertEqual(self.roundtrip(Signed(), 0.0), 0.0)
        self.assertEqual(self.roundtrip(Signed(), -1.0), -1.0)
        self.assertTrue(self.roundtrip(Flag(), True))
        self.assertAlmostEqual(self.roundtrip(Wide16(), 0.5), 0.5, places=4)

    def test_enum_unknown_fails_safe(self):
        e = Enum((0, 100), 0)
        self.assertEqual(e.decode(bytes([101]), 0), 0)
        self.assertEqual(e.decode(bytes([100]), 0), 100)

    def test_clamped(self):
        self.assertEqual(self.roundtrip(Level(), 2.0), 1.0)
        self.assertEqual(self.roundtrip(Level(), -1.0), 0.0)


class LayoutTest(unittest.TestCase):
    def test_offsets_and_footprint(self):
        lay = Layout([('a', U8()), ('b', Wide16()), ('c', U8())])
        self.assertEqual(lay.footprint, 4)
        self.assertEqual(lay.offset('c'), 3)

    def test_footprint_must_fit(self):
        with self.assertRaises(ValueError):
            p.LAYOUT.encode({}, bytearray(1))


class CommandTest(unittest.TestCase):
    def test_roundtrip_with_offset(self):
        cmd = Command(p.LAYOUT, mode=p.MODE_RUN, level=1.0, r=7)
        frame = cmd.to_frame(base=9)
        self.assertEqual(frame[9 + p.LAYOUT.offset('mode')], p.MODE_RUN)
        self.assertEqual(frame[9 + p.LAYOUT.offset('level')], 255)
        self.assertEqual(Command.from_frame(p.LAYOUT, frame, base=9), cmd)

    def test_unknown_channel_rejected(self):
        with self.assertRaises(KeyError):
            Command(p.LAYOUT).nope = 1


class DeviceTest(unittest.TestCase):
    def setUp(self):
        # desktop shims for MicroPython's tick functions
        time.ticks_ms = lambda: int(time.monotonic() * 1000)
        time.ticks_diff = lambda a, b: a - b

    def test_dispatch_and_timeout(self):
        d = DmxDevice(p.LAYOUT)
        seen, anys = [], []
        d.watch('r', seen.append)
        d.on_change(lambda v: anys.append(dict(v)))
        frame = Command(p.LAYOUT, mode=p.MODE_RUN, level=1.0, r=5).to_frame()
        d.update(frame)
        d.update(frame)  # unchanged: no extra dispatch
        self.assertTrue(d.valid)
        self.assertEqual(seen, [5])
        self.assertEqual(len(anys), 1)
        self.assertEqual(d.values['mode'], p.MODE_RUN)
        d._last_ms -= SIGNAL_TIMEOUT_MS + 1
        d.check_timeout()
        self.assertFalse(d.valid)
        self.assertEqual(d.values['mode'], p.MODE_STOP)
        self.assertEqual(seen, [5, 0])
        self.assertEqual(len(anys), 2)

    def test_watch_unknown_name(self):
        with self.assertRaises(KeyError):
            DmxDevice(p.LAYOUT).watch('nope', print)


if __name__ == '__main__':
    unittest.main()
