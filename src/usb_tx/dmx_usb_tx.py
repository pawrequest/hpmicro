"""Minimal DMX512 sender for a CH340 USB-serial + MAX485 (DE/RE hardwired high).

Light: 3-channel mode, start address 1 -> ch1=R, ch2=G, ch3=B.

    pip install pyserial
    python dmx_usb_tx.py --port COM8 255 0 0          # solid red
    python dmx_usb_tx.py 0 0 255 --seconds 10         # blue for 10 s
    python dmx_usb_tx.py --demo                       # cycle colours
"""

import argparse
import colorsys
import time
from argparse import Namespace

import serial

from shared.config import COM_PORT

UNIVERSE_SIZE = 512
FRAME_INTERVAL = 0.025  # ~40 fps


class Dmx:
    def __init__(self, port):
        # DMX512: 250 kbaud, 8 data bits, no parity, 2 stop bits
        print(f"Opening {port} at 250000 baud, 8N2")
        self.ser = serial.Serial(
            port, baudrate=250000, bytesize=8, parity=serial.PARITY_NONE, stopbits=2
        )
        print(f"Opened {port}")
        self.data = bytearray(UNIVERSE_SIZE)

    def set(self, channel, value):
        self.data[channel - 1] = max(0, min(255, int(value)))

    def send(self):
        # Fake the BREAK: a 0x00 byte at 90909 baud 8N1 is ~99us low then a ~11us
        # high (mark after break). More reliable on CH340 than break_condition.
        self.ser.baudrate = 90909
        self.ser.stopbits = 1
        self.ser.write(b"\x00")
        self.ser.flush()
        self.ser.baudrate = 250000
        self.ser.stopbits = 2
        self.ser.write(b"\x00" + bytes(self.data))  # start code + slots
        self.ser.flush()

    def close(self):
        self.ser.close()
        print("Port closed")


def main(args: Namespace | None = None):
    args = args or parse_args()
    print(
        f"Starting: port={args.port} address={args.address} "
        f"mode={'demo' if args.demo else f'static rgb={args.rgb} for {args.seconds}s'}"
    )
    dmx = Dmx(args.port)
    last_log = 0.0
    try:
        start = time.time()
        while args.demo or time.time() - start < args.seconds:
            if args.demo:
                r, g, b = (
                    c * 255 for c in colorsys.hsv_to_rgb((time.time() / 5) % 1, 1, 1)
                )
            else:
                r, g, b = args.rgb
            for i, v in enumerate((r, g, b)):
                dmx.set(args.address + i, v)
            dmx.send()
            now = time.time()
            if now - last_log >= 1:
                print(f"Sending R={int(r)} G={int(g)} B={int(b)}")
                last_log = now
            time.sleep(FRAME_INTERVAL)
        print("Finished")
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        print("Blacking out lights")
        for i in range(3):
            dmx.set(args.address + i, 0)
        dmx.send()
        dmx.close()


def parse_args(argv=None) -> Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--port", default=COM_PORT, help=f"serial port (default {COM_PORT})")
    p.add_argument(
        "--address", type=int, default=1, help="DMX start address (default 1)"
    )
    p.add_argument(
        "--seconds", type=float, default=5, help="how long to hold the colour"
    )
    p.add_argument("--demo", action="store_true", help="cycle through hues")
    p.add_argument("rgb", nargs="*", type=int, metavar="R G B", help="0-255 each")
    args = p.parse_args(argv)
    if not args.demo and len(args.rgb) != 3:
        p.error("give R G B values, or use --demo")
    return args


if __name__ == "__main__":
    main(Namespace(port=COM_PORT, address=1, seconds=1000, demo=True, rgb=[]))
