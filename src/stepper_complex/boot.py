import time

import network
import webrepl

from device_config import IP_ADDRESS
from shared.wifi_config import (
    DNS,
    GATEWAY,
    SUBNET,
    PASSWORD,
    SSID,
    WIFI_TIMEOUT_SECONDS,
)


def connect_wifi(static: bool = False):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        if static:
            wlan.ifconfig((IP_ADDRESS, SUBNET, GATEWAY, DNS))
        wlan.connect(SSID, PASSWORD)
        deadline = time.ticks_add(time.ticks_ms(), WIFI_TIMEOUT_SECONDS * 1000)

        while not wlan.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
            time.sleep_ms(250)

    if not wlan.isconnected():
        raise RuntimeError("Could not connect to Wi-Fi")

    print("Wi-Fi connected:", wlan.ifconfig()[0])
    return wlan


connect_wifi(static=True)
webrepl.start()
