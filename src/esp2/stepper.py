from shared import config

from stepper_redox import StepperRedox

STEPS_PER_PROP_REV = config.PROP_STEPS_PER_REV


class Stepper:
    def __init__(self):
        self.s = StepperRedox()
        self.s.stop()  # stepper_1.__init__ starts tracking immediately

    @property
    def enabled(self):
        return self.s.enabled

    def enable(self, on):
        self.s.enable(on)

    @property
    def position(self):
        return self.s.pos

    @position.setter
    def position(self, steps):
        self.s.pos = int(steps)
        self.s.target_pos = self.s.pos

    @property
    def rate(self):
        """Signed steps/s currently being output (0 when stopped)."""
        s = self.s
        if not s.timer_is_running:
            return 0.0
        if s.free_run_mode:
            return float(s.free_run_mode * s.steps_per_sec)
        d = s.target_pos - s.pos
        return float(s.steps_per_sec if d > 0 else -s.steps_per_sec if d < 0 else 0)

    def _same_speed(self, sps):
        cur = self.s.steps_per_sec
        return abs(cur - sps) <= max(5, 0.05 * cur)

    def goto_steps(self, target, sps):
        """Track an absolute step target at sps steps/s (stepper_1 track_target mode)."""
        s = self.s
        target = int(round(target))
        if target == s.pos:
            self.stop()
            return
        s.target_pos = target
        if s.timer_is_running and s.free_run_mode == 0 and self._same_speed(sps):
            return
        s.steps_per_sec = sps
        s.track_target()

    def run(self, sps):
        """Free-run, signed steps/s (stepper_1 free_run mode)."""
        s = self.s
        d = 1 if sps > 0 else -1
        sps = abs(sps)
        if s.timer_is_running and s.free_run_mode == d and self._same_speed(sps):
            return
        s.steps_per_sec = sps
        s.free_run(d)

    def stop(self):
        s = self.s
        if s.timer_is_running or s.free_run_mode:
            s.stop()
        s.target_pos = s.pos

    stop_now = stop
