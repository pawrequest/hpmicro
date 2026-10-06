# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import time

import network
import webrepl
from shared.wifi_config import (
    DNS,
    GATEWAY,
    IP_2,
    SUBNET,
    WIFI_PASSWORD,
    WIFI_SSID,
    WIFI_TIMEOUT_SECONDS,
)


def connect_wifi(static: bool = False):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        if static:
            wlan.ifconfig((IP_2, SUBNET, GATEWAY, DNS))
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        deadline = time.ticks_add(time.ticks_ms(), WIFI_TIMEOUT_SECONDS * 1000)

        while not wlan.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
            time.sleep_ms(250)

    if not wlan.isconnected():
        raise RuntimeError("Could not connect to Wi-Fi")

    print("Wi-Fi connected:", wlan.ifconfig()[0])
    return wlan


connect_wifi(static=True)
webrepl.start()
