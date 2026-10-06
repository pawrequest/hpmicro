import gc
from pprint import pprint

from micropython import alloc_emergency_exception_buf

import dmx512_rx_pr
import simple_config
from shared.config import DMX_RX_ENABLE_PIN, DMX_RX_PIN

# Environment Setup
gc.threshold(16384)  # Run Garbage collection everytime 16KB is allocated
alloc_emergency_exception_buf(512)  # Allocate Emergency Exception Buffer


def parse_dmx_data(dmx_data):
    if not all(isinstance(x, int) for x in dmx_data):
        raise ValueError("All elements in dmx_data must be integers")
    match dmx_data:
        case a, b, c:
            ...
        case _:
            pass


def printer(dmx_data):
    pprint(dmx_data)
    print(f"{type(dmx_data)=}")


def dmxstatuschange(status):
    print("status changed :", status)


def main_loop():
    dmxrx_deviceaddress = simple_config.dmx_address  # Our device Base DMX Address
    dmxrx_devicechannels = simple_config.dmx_channels  # How many channels we care about

    print("INFO: Starting Main Loop")
    dmx = dmx512_rx_pr.DMX(
        dmxrx_deviceaddress,
        dmxrx_devicechannels,
        DMX_RX_PIN,
        de_re_pin=DMX_RX_ENABLE_PIN,
    )
    dmx.set_updatefunction(printer)
    dmx.set_statusfunction(dmxstatuschange)

    while True:
        if dmx.loop() == 0:  # If 0 we have been offline for an extended period
            print("timeout")
            break
