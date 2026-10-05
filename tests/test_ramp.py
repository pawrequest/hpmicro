import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from esp_rx import ramp


class RampTests(unittest.TestCase):
    def test_slew_limits(self):
        self.assertEqual(ramp.slew(0, 100, 10, 1), 10)
        self.assertEqual(ramp.slew(0, 5, 10, 1), 5)
        self.assertEqual(ramp.slew(0, -100, 10, 1), -10)

    def test_modes(self):
        self.assertEqual(ramp.mode_from_dmx(0), "stop")
        self.assertEqual(ramp.mode_from_dmx(64), "speed")
        self.assertEqual(ramp.mode_from_dmx(128), "position")
        self.assertEqual(ramp.mode_from_dmx(255), "home")

    def test_speed_fraction(self):
        self.assertEqual(ramp.speed_fraction(128), 0)
        self.assertEqual(ramp.speed_fraction(255), 1.0)
        self.assertEqual(ramp.speed_fraction(0), -1.0)

    def test_position_fraction(self):
        self.assertEqual(ramp.position_fraction(0, 0), 0)
        self.assertEqual(ramp.position_fraction(255, 255), 1.0)

    def test_shortest(self):
        self.assertAlmostEqual(ramp.shortest_delta(10, 350, 360), 20)
        self.assertAlmostEqual(ramp.shortest_delta(350, 10, 360), -20)

    def test_approach_converges(self):
        pos, v, dt = 0.0, 0.0, 0.01
        target, vmax, acc = 9600.0, 4800.0, 4800.0
        for _ in range(3000):
            rem = target - pos
            if abs(rem) < 1 and abs(v) < 50:
                break
            v = ramp.slew(v, ramp.approach_velocity(rem, vmax, acc), acc, dt)
            pos += v * dt
        self.assertLess(abs(target - pos), 50)


if __name__ == "__main__":
    unittest.main()
