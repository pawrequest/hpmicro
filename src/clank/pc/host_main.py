"""Laptop entry point: send clank Commands over the USB DMX adapter.

Run from the `src` directory:
    python -m clank.host_main --level 1.0              # MODE_RUN at full level
    python -m clank.host_main --mode stop              # MODE_STOP
    python -m clank.host_main --demo                   # triangle-wave level ramp
    python -m clank.host_main --port COM8 --seconds 10
"""

import argparse
import math
import time
from argparse import Namespace

from shared.config import COM_PORT, DMX_ADDRESS

from shared import dmx_util as dmx_util
from clank.pc.dmx_usb_tx import FRAME_INTERVAL, Dmx
from clank.pc.host import Command

MODES = {'stop': dmx_util.MODE_STOP, 'run': dmx_util.MODE_RUN}
DEMO_PERIOD_S = 4.0
COLOUR_CYCLE_S = 6.0  # seconds per full hue rotation


def demo_level(t: float) -> float:
    return abs(math.sin(math.pi * t / DEMO_PERIOD_S))


def main() -> None:
    # args = parse_args()

    cmd = Command(dmx_util.LAYOUT)
    dmx = Dmx(COM_PORT)
    start = time.monotonic()
    channel = 1
    base = 0
    seconds = 0
    try:
        demo = True
        while seconds <= 0 or time.monotonic() - start < seconds:
            if demo:
                cmd.mode = dmx_util.MODE_RUN
                t = time.monotonic() - start
                cmd.level = 1.0
                cmd.hue = (t / COLOUR_CYCLE_S) % 1.0
            cmd.write_into(dmx.data, DMX_ADDRESS)
            dmx.send()
            time.sleep(FRAME_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        Command(dmx_util.LAYOUT, mode=dmx_util.MODE_STOP).write_into(dmx.data, DMX_ADDRESS)
        dmx.send()  # leave the receiver in a safe state
        dmx.close()


def parse_args() -> Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--port', default=COM_PORT)
    ap.add_argument('--mode', choices=MODES, default='run')
    ap.add_argument('--level', type=float, default=1.0, help='0..1')
    ap.add_argument('--base', type=int, default=0, help='0-based channel offset')
    ap.add_argument('--demo', action='store_true', help='ramp level up and down')
    ap.add_argument('--seconds', type=float, default=0, help='0 = until Ctrl+C')
    args = ap.parse_args()
    return args


if __name__ == '__main__':
    main()
