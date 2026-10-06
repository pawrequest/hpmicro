"""ESP32 entry point: DMX in -> DmxDevice (layout-driven) -> RGB LED.

Deploy flat to the device root:
    dmx_device.py  dmx_esp_rx.py  main.py
    shared/dmx_layout.py  shared/dmx_util.py  shared/config.py

Behaviour: MODE_RUN -> LED shows the colour for hue, scaled by level; MODE_STOP, loss of signal
or a DMX offline status -> LED off (failsafe defaults from the layout).
"""

import gc

import machine
import neopixel
from micropython import alloc_emergency_exception_buf

from dmx_device import DmxDevice
from dmx_esp_rx import DMX
from shared import dmx_util
from shared.config import DMX_ADDRESS, DMX_RX_ENABLE_PIN, DMX_RX_PIN, ESP_RGB_LED_PIN

gc.threshold(16384)
alloc_emergency_exception_buf(512)

led = neopixel.NeoPixel(machine.Pin(ESP_RGB_LED_PIN), 1)


def hsv_rgb(h):
    """Hue 0..1 at full saturation/value -> (r, g, b); MicroPython has no colorsys."""
    h = (h % 1.0) * 6
    i = int(h)
    f = int((h - i) * 255)
    return ((255, f, 0), (255 - f, 255, 0), (0, 255, f), (0, 255 - f, 255), (f, 0, 255), (255, 0, 255 - f))[i % 6]


def apply(v):
    if v['mode'] == dmx_util.MODE_RUN:
        k = v['level']
        r, g, b = hsv_rgb(v['hue'])
        led[0] = (int(r * k), int(g * k), int(b * k))
    else:
        led[0] = (0, 0, 0)
    led.write()


def main():
    device = DmxDevice(dmx_util.LAYOUT)
    device.on_change(apply)
    dmx = DMX(DMX_ADDRESS, dmx_util.FOOTPRINT, DMX_RX_PIN, de_re_pin=DMX_RX_ENABLE_PIN)
    print("clank: running")
    try:
        device.run(dmx)
    finally:
        led[0] = (0, 0, 0)
        led.write()


main()
