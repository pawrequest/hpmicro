"""ESP32 entry point: DMX in -> protocol State -> PWM LED (placeholder action).

Deploy flat to the device root:
    protocol.py  device.py  dmx_esp_rx.py  main.py
    shared/config.py   (for DMX_RX_PIN / DMX_RX_ENABLE_PIN)

Behaviour: MODE_RUN -> LED shows CH_RED/GREEN/BLUE scaled by CH_LEVEL; MODE_STOP, loss of signal
or a DMX offline status -> LED off.
"""

import gc

import machine
import neopixel
from micropython import alloc_emergency_exception_buf

from dmx_esp_rx import DMX
from dmx_state import DmxState
from shared import dmx_util
from shared.config import DMX_RX_ENABLE_PIN, DMX_RX_PIN, ESP_RGB_LED_PIN, DMX_ADDRESS

gc.threshold(16384)
alloc_emergency_exception_buf(512)

state = DmxState()
led = neopixel.NeoPixel(machine.Pin(ESP_RGB_LED_PIN), 1)


def on_update(channels):
    state.update(channels)
    # print(channels)


def on_status(status):
    # 2 = online; anything else means the signal is gone, so fail safe
    if status != 2:
        state.valid = False
        state.mode = dmx_util.MODE_STOP
        state.level = 0.0


def apply(s):
    """Placeholder action: map state to hardware."""
    if s.valid and s.mode == dmx_util.MODE_RUN:
        k = s.level
        led[0] = (int(s.r * k), int(s.g * k), int(s.b * k))
    else:
        led[0] = (0, 0, 0)
    led.write()


def main():
    dmx = DMX(DMX_ADDRESS, dmx_util.FOOTPRINT, DMX_RX_PIN, de_re_pin=DMX_RX_ENABLE_PIN)
    dmx.set_updatefunction(on_update)
    dmx.set_statusfunction(on_status)
    print("clank: running")
    try:
        while True:
            dmx.loop()
            state.check_timeout()
            apply(state)
    finally:
        led[0] = (0, 0, 0)
        led.write()


main()
