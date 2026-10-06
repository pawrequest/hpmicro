# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import time

import network
import webrepl
from shared.webrepl_cfg import PASS as WEBREPL_PASS

webrepl.start(password=WEBREPL_PASS)


def connect_wifi(static: bool = False):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Connecting to Wi-Fi...")
    from shared.wifi_config import (
        DNS,
        GATEWAY,
        IP_RX,
        SUBNET,
        WIFI_PASSWORD,
        WIFI_SSID,
        WIFI_TIMEOUT_SECONDS,
    )

    if not wlan.isconnected():
        print("not connected, attempting to connect to Wi-Fi...")
        wlan.disconnect()  # cancel any pending connect from before the soft reboot
        time.sleep_ms(200)
        if static:
            print("fetching static IP configuration from wifi_config.py")
            wlan.ifconfig((IP_RX, SUBNET, GATEWAY, DNS))
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        deadline = time.ticks_add(time.ticks_ms(), WIFI_TIMEOUT_SECONDS * 1000)

        while not wlan.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
            print("waiting for Wi-Fi...")
            time.sleep_ms(250)

    if not wlan.isconnected():
        raise RuntimeError("Could not connect to Wi-Fi")

    print("Wi-Fi connected:", wlan.ifconfig()[0])
    return wlan


connect_wifi(static=True)
