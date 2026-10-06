from time import ticks_diff, ticks_ms

from esp_rx.inputs.base import Input

from esp_rx import config


class ReplInput(Input):
    """Control from the REPL/WebREPL:  ctl.speed(0.5)  ctl.goto(90)  ctl.home()  ctl.stop()"""

    def __init__(self, cmd):
        Input.__init__(self, cmd)
        self.prop = None  # set by main for status()
        self._last = ticks_ms()

    def _touch(self):
        self._last = ticks_ms()
        self.cmd.valid = True

    def poll(self):
        wd = config.REPL_WATCHDOG_S
        if (
            wd is not None
            and self.cmd.valid
            and ticks_diff(ticks_ms(), self._last) > wd * 1000
        ):
            self.cmd.valid = False

    def speed(self, x):
        """Continuous rotation, -1..1 of max speed (negative = reverse)."""
        c = self.cmd
        c.speed = max(-1.0, min(1.0, float(x)))
        c.mode = "speed"
        self._touch()

    def rpm(self, rpm):
        """Continuous rotation in prop RPM (clamped to MAX_SPEED_RPM)."""
        self.speed(rpm / config.MAX_SPEED_RPM)

    def goto(self, deg):
        """Move to prop angle in degrees."""
        c = self.cmd
        c.position_deg = float(deg)
        c.mode = "position"
        self._touch()

    def home(self):
        self.cmd.mode = "home"
        self._touch()

    def stop(self):
        """Decelerate to a stop and hold."""
        self.cmd.mode = "stop"
        self.cmd.speed = 0.0
        self._touch()

    def limit(self, pct):
        """Speed limit as percent of max speed (1-100)."""
        self.cmd.limit = max(0.01, min(1.0, pct / 100.0))

    def status(self):
        p = self.prop
        c = self.cmd
        d = {
            "mode": c.mode,
            "speed": c.speed,
            "target_deg": c.position_deg,
            "limit": c.limit,
        }
        if p is not None:
            d["state"] = p.mode
            d["angle_deg"] = p.angle_deg()
            d["step_hz"] = p.stepper.rate
            d["homed"] = p.homed
        return d
