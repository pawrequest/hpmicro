"""ESP32 (MicroPython) side: layout-driven device with signal-loss failsafe.

Hardware access stays out of here (the receiver is passed to `run`), so the class is
testable on a desktop. Register behaviour with `watch` / `on_change`:

    dev = DmxDevice(LAYOUT)
    dev.watch('speed', lambda v: motor.set(v))     # one channel, fires when it changes
    dev.on_change(lambda values: apply(values))    # any channel, fires once per change
    dev.run(DMX(...))
"""

import time

SIGNAL_TIMEOUT_MS = 500


class DmxDevice:
    def __init__(self, layout):
        self.layout = layout
        self.values = layout.defaults()
        self.valid = False  # False => no recent frame; values are the failsafe defaults
        self._scratch = layout.defaults()
        self._last_ms = 0
        self._watch = {}
        self._any = []

    def watch(self, name, fn):
        if name not in self.layout.index:
            raise KeyError(name)
        self._watch.setdefault(name, []).append(fn)

    def on_change(self, fn):
        self._any.append(fn)

    def update(self, frame, base=0):
        """Decode `frame` and dispatch handlers for anything that changed."""
        self._last_ms = time.ticks_ms()
        self.layout.decode(frame, base, self._scratch)
        self._commit(self._scratch, True)

    def failsafe(self):
        self._commit(self.layout.defaults(), False)

    def check_timeout(self):
        if self.valid and time.ticks_diff(time.ticks_ms(), self._last_ms) > SIGNAL_TIMEOUT_MS:
            self.failsafe()

    def _commit(self, new, valid):
        changed = valid != self.valid
        self.valid = valid
        values = self.values
        for n in self.layout.names:
            v = new[n]
            if values[n] != v:
                values[n] = v
                changed = True
                for fn in self._watch.get(n, ()):
                    fn(v)
        if changed:
            for fn in self._any:
                fn(values)

    def _on_status(self, status):
        # 2 = online; anything else means the signal is gone
        if status != 2:
            self.failsafe()

    def run(self, dmx):
        """Drive a receiver exposing set_updatefunction/set_statusfunction/loop."""
        dmx.set_updatefunction(self.update)
        dmx.set_statusfunction(self._on_status)
        try:
            while True:
                dmx.loop()
                self.check_timeout()
        finally:
            self.failsafe()
