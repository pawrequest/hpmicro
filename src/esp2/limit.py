import config
from machine import Pin


class LimitSwitch:
    """Optional limit/hall input. If disabled, never triggers."""

    def __init__(self):
        self.enabled = config.LIMIT_ENABLED and config.LIMIT_PIN is not None
        self._pin = None
        if self.enabled:
            pull = Pin.PULL_UP if config.LIMIT_PULL_UP else None
            self._pin = Pin(config.LIMIT_PIN, Pin.IN, pull)

    def triggered(self):
        if not self.enabled:
            return False
        a = self._pin.value()
        b = self._pin.value()
        return a == b == config.LIMIT_ACTIVE_LEVEL
