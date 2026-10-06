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
        # marking the data
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

