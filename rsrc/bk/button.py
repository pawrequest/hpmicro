"""
Momentary push-button helper for a pin wired to GND (active-low, uses internal pull-up).
"""

import time

import machine
import micropython
from config import BUTTON_DEBOUNCE_MS, BUTTON_PIN

micropython.alloc_emergency_exception_buf(100)


class Button:
    def __init__(self, callback, pin=BUTTON_PIN, debounce_ms=BUTTON_DEBOUNCE_MS):
        """
        callback: function called with no args when the button is pressed.
        pin: GPIO number (or machine.Pin) connected to the button, other side to GND.
        debounce_ms: minimum time between accepted presses, to ignore contact bounce.
        """
        if not isinstance(pin, machine.Pin):
            pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)

        self.pin = pin
        self.callback = callback
        self.debounce_ms = debounce_ms
        self._last_press_ms = 0

        self.pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self._on_irq)

    def _on_irq(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_press_ms) < self.debounce_ms:
            return
        self._last_press_ms = now
        if pin.value() == 0:
            self.callback()

    def deinit(self):
        self.pin.irq(handler=None)
