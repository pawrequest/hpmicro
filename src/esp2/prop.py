"""Turns the shared Command into motor motion.

Motion is constant-speed (stepper_1 has no ramps): the desired mode/speed/target is
applied to the stepper only when it changes, so the step timer is left alone otherwise.
"""

from time import ticks_ms, ticks_diff

import config
import ramp
from stepper import STEPS_PER_PROP_REV

_REV = STEPS_PER_PROP_REV
_MAX_SPS = config.SPEED_SPS
_HOME_SPS = config.HOME_SPEED_RPM / 60.0 * _REV
_HOME_OFFSET = config.HOME_OFFSET_DEG / 360.0 * _REV


class Prop:
    def __init__(self, cmd, stepper, limit):
        self.cmd = cmd
        self.stepper = stepper
        self.limit = limit
        self.mode = "idle"
        self.homed = False
        self._ever_valid = False
        self._home_done = False
        self._idle_since = ticks_ms()

    def update(self, dt=0):
        c = self.cmd
        st = self.stepper

        if not c.valid:
            self.mode = "lost" if self._ever_valid else "idle"
            st.stop()
        else:
            self._ever_valid = True
            mode = c.mode
            self.mode = mode
            vmax = _MAX_SPS * c.limit
            if mode != "home":
                self._home_done = False
            if mode == "speed":
                self._speed(c.speed * vmax)
            elif mode == "position":
                self._position(c.position_deg, vmax)
            elif mode == "home":
                self._home()
            else:
                st.stop()
        self._idle_handling()

    def _enable(self):
        if not self.stepper.enabled:
            self.stepper.enable(True)

    def _speed(self, sps):
        if abs(sps) < config.MIN_STEP_HZ:
            self.stepper.stop()
            return
        self._enable()
        self.stepper.run(sps)

    def _position(self, deg, vmax):
        st = self.stepper
        if config.REQUIRE_HOMED and not self.homed:
            st.stop()
            return
        pos = st.position
        target = round(deg / 360.0 * _REV)
        if config.POSITION_SHORTEST_PATH:
            rem = round(ramp.shortest_delta(target, pos, _REV))
        else:
            rem = target - pos
        if rem == 0:
            st.stop()
            return
        self._enable()
        st.goto_steps(pos + rem, max(vmax, config.MIN_STEP_HZ))

    def _home(self):
        st = self.stepper
        if self._home_done:
            st.stop()
        elif self.limit.enabled and not self.limit.triggered():
            self._enable()
            st.run(config.HOME_DIRECTION * _HOME_SPS)
        else:
            # Switch found (or no switch: zero in place).
            st.stop()
            st.position = _HOME_OFFSET if self.limit.enabled else 0
            self.homed = True
            self._home_done = True

    def _idle_handling(self):
        st = self.stepper
        if st.rate != 0.0:
            self._idle_since = ticks_ms()
        elif (
                config.DISABLE_AFTER_IDLE_S is not None
                and st.enabled
                and ticks_diff(ticks_ms(), self._idle_since)
                > config.DISABLE_AFTER_IDLE_S * 1000
        ):
            st.enable(False)

    def angle_deg(self):
        return self.stepper.position / _REV * 360.0
