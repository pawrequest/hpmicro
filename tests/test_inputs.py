import os
import sys
import time
import types
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

# Host shims for MicroPython-only APIs
time.ticks_ms = lambda: int(time.monotonic() * 1000)
time.ticks_us = lambda: int(time.monotonic() * 1e6)
time.ticks_diff = lambda a, b: a - b
time.sleep_us = lambda us: None


class _Pin:
    OUT = IN = PULL_UP = IRQ_FALLING = IRQ_RISING = 0

    def __init__(self, *a, **k):
        pass

    def value(self, v=None):
        return 0


class _Timer:
    PERIODIC = 1

    def __init__(self, *a, **k):
        pass

    def init(self, **k):
        pass

    def deinit(self):
        pass


machine = types.ModuleType("machine")
machine.Pin = _Pin
machine.Timer = _Timer
sys.modules["machine"] = machine

from esp_rx import config
from esp_rx.command import Command
from esp_rx.inputs.dmx_input import DmxInput
from esp_rx.inputs.repl_input import ReplInput
from esp_rx.prop import Prop
from esp_rx.stepper import Stepper, STEPS_PER_PROP_REV


class FakeDmx:
    def __init__(self, ch, ok=True):
        self.ch = ch
        self.ok = ok

    def service(self):
        pass

    def signal_ok(self):
        return self.ok

    def channel(self, off):
        return self.ch.get(off, 0)


class DmxInputTests(unittest.TestCase):
    def test_mapping(self):
        c = Command()
        d = FakeDmx(
            {
                config.CH_MODE: 130,
                config.CH_VALUE: 255,
                config.CH_FINE: 255,
                config.CH_LIMIT: 0,
            }
        )
        DmxInput(c, d).poll()
        self.assertTrue(c.valid)
        self.assertEqual(c.mode, "position")
        self.assertAlmostEqual(c.position_deg, 360.0)
        self.assertEqual(c.limit, 1.0)

    def test_loss_invalidates(self):
        c = Command()
        d = FakeDmx({}, ok=False)
        DmxInput(c, d).poll()
        self.assertFalse(c.valid)


class ReplInputTests(unittest.TestCase):
    def test_api(self):
        c = Command()
        r = ReplInput(c)
        self.assertFalse(c.valid)
        r.speed(2)
        self.assertEqual((c.mode, c.speed, c.valid), ("speed", 1.0, True))
        r.rpm(config.MAX_SPEED_RPM / 2)
        self.assertAlmostEqual(c.speed, 0.5)
        r.goto(90)
        self.assertEqual((c.mode, c.position_deg), ("position", 90.0))
        r.limit(50)
        self.assertEqual(c.limit, 0.5)
        r.home()
        self.assertEqual(c.mode, "home")
        r.stop()
        self.assertEqual((c.mode, c.speed), ("stop", 0.0))

    def test_watchdog(self):
        config.REPL_WATCHDOG_S = 0
        try:
            c = Command()
            r = ReplInput(c)
            r.speed(0.5)
            time.sleep(0.01)
            r.poll()
            self.assertFalse(c.valid)
        finally:
            config.REPL_WATCHDOG_S = None


class _NoLimit:
    enabled = False

    def triggered(self):
        return False


def _run(p, st, n, steps_per_tick=10):
    for _ in range(n):
        p.update()
        for _ in range(steps_per_tick):  # simulate timer callbacks
            st.s._timer_callback(None)


class PropTests(unittest.TestCase):
    def setUp(self):
        self.c = Command()
        self.st = Stepper()
        self.p = Prop(self.c, self.st, _NoLimit())

    def test_idle_timer_is_off(self):
        self.assertFalse(self.st.s.timer_is_running)

    def test_goto_lands_exactly_and_returns(self):
        c, st, p = self.c, self.st, self.p
        c.valid, c.mode, c.position_deg = True, "position", 90.0
        p.update()
        self.assertGreater(abs(st.rate), 0)  # starts immediately, at full speed
        self.assertEqual(abs(st.rate), config.SPEED_SPS)
        _run(p, st, 500)
        self.assertEqual(st.position, round(STEPS_PER_PROP_REV / 4))
        self.assertEqual(st.rate, 0)
        self.assertFalse(st.s.timer_is_running)
        for deg in (0.0, 360.0, 0.0, 360.0):
            c.position_deg = deg
            _run(p, st, 2000)
            self.assertEqual(st.position, round(deg / 360 * STEPS_PER_PROP_REV))

    def test_timer_not_reinitialised_while_moving(self):
        c, st, p = self.c, self.st, self.p
        inits = []
        real = st.s.timer.init
        st.s.timer.init = lambda **k: (inits.append(k), real(**k))
        c.valid, c.mode, c.position_deg = True, "position", 90.0
        for _ in range(50):
            p.update()
        self.assertEqual(len(inits), 1)

    def test_speed_mode_and_stop_on_loss(self):
        c, st, p = self.c, self.st, self.p
        c.valid, c.mode, c.speed = True, "speed", -0.5
        _run(p, st, 10)
        self.assertAlmostEqual(st.rate, -0.5 * config.SPEED_SPS, delta=1)
        self.assertLess(st.position, 0)
        c.valid = False
        p.update()
        self.assertEqual(st.rate, 0)
        self.assertEqual(p.mode, "lost")

if __name__ == "__main__":
    unittest.main()
