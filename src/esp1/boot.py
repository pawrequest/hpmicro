# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import time
from secrets import DNS, GATEWAY, IP, SUBNET, WIFI_PASSWORD, WIFI_SSID

import network
import webrepl

from config import WIFI_TIMEOUT_SECONDS

webrepl.start()


def connect_wifi(static: bool = False):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Connecting to Wi-Fi...")
    if static:
        print('fetching static IP configuration from secrets.py')
        wlan.ifconfig((IP, SUBNET, GATEWAY, DNS))

    if not wlan.isconnected():
        print('not connected, attempting to connect to Wi-Fi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        deadline = time.ticks_add(time.ticks_ms(), WIFI_TIMEOUT_SECONDS * 1000)

        while not wlan.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
            print('waiting for Wi-Fi...')
            time.sleep_ms(250)

    if not wlan.isconnected():
        raise RuntimeError("Could not connect to Wi-Fi")

    print("Wi-Fi connected:", wlan.ifconfig()[0])
    return wlan


connect_wifi(static=True)
