"""Desktop (CPython) counterpart to dmx_demo.py.

dmx_demo.py drives a MicroPython board's UART directly, toggling a
send/receive-enable pin on a MAX485 transceiver. Here we have no such pin:
a USB-to-RS485 (MAX485) adapter on COM8 is used instead, so a plain
pyserial connection stands in for the UART.

DMX break/mark-after-break generation mirrors dmx_demo.py's approach:
drop to a slow baud rate and send a 0x00 byte so the line is held low
longer than the minimum DMX break (92us), then switch back to the real
250000 baud DMX rate to send the data frame.
"""

import random
import time

import serial

from config import BREAK_BAUDRATE, DMX_BAUDRATE, FRAME_DELAY_S, PORT


def send_dmx_frame(ser, red, green, blue):
    """Send one DMX frame (start code 0 + RGB on channels 1-3)."""
    frame = bytes((0, red, green, blue))

    # Break: hold the line low longer than a normal byte by sending a
    # null byte at a much slower baud rate.
    ser.baudrate = BREAK_BAUDRATE
    ser.write(b"\x00")
    ser.flush()

    # Mark-after-break + the actual DMX data at full speed.
    ser.baudrate = DMX_BAUDRATE
    ser.write(frame)
    ser.flush()


# def send_dmx_frame(ser, red, green, blue):
#     frame = bytes((0, red, green, blue))
#     ser.break_condition = True
#     time.sleep(0.001)  # break, at least 92us
#     ser.break_condition = False
#     time.sleep(0.0001)  # mark after break, at least 12us
#     ser.write(frame)
#     ser.flush()


def effect_fade(ser, colors, steps=256, delay_s=FRAME_DELAY_S):
    """Fade smoothly between the colors, then loop back to the first."""
    print("Effect fade")
    for start, end in zip(colors, colors[1:] + colors[:1]):
        for step in range(steps):
            color = tuple(
                start[channel] + (end[channel] - start[channel]) * step // (steps - 1)
                for channel in range(3)
            )
            send_dmx_frame(ser, *color)
            time.sleep(delay_s)


def effect_color_hold(ser, colors, hold_s=0.7):
    """Show each color at full intensity for a fixed interval."""
    print("Effect color hold")
    for color in colors:
        send_dmx_frame(ser, *color)
        time.sleep(hold_s)


def effect_pulse(ser, color, steps=100, delay_s=0.01):
    """Fade one color up to full brightness and back down."""
    print("Effect pulse")
    for brightness in range(steps + 1):
        level = brightness * 255 // steps
        send_dmx_frame(ser, *(channel * level // 255 for channel in color))
        time.sleep(delay_s)

    for brightness in range(steps - 1, -1, -1):
        level = brightness * 255 // steps
        send_dmx_frame(ser, *(channel * level // 255 for channel in color))
        time.sleep(delay_s)


def effect_random_colors(ser, count=20, hold_s=0.35):
    """Jump between randomly chosen RGB colors."""
    print("Effect random colors")
    for _ in range(count):
        color = tuple(random.getrandbits(8) for _ in range(3))
        send_dmx_frame(ser, *color)
        time.sleep(hold_s)


palette = (
    (255, 0, 0),
    (255, 96, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 255),
    (0, 0, 255),
    (160, 0, 255),
)


def demo(ser):
    """Loop the same effects sequence as dmx_demo.py's background worker."""
    print("Effect demo")
    while True:
        effect_random_colors(ser)
        effect_pulse(ser, (255, 40, 0))
        effect_fade(ser, palette)
        effect_color_hold(ser, ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)))


if __name__ == "__main__":
    with serial.Serial(
        PORT,
        DMX_BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
    ) as ser:
        try:
            demo(ser)
        except KeyboardInterrupt:
            pass
