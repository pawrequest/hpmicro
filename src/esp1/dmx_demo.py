import _thread
from time import sleep_ms, sleep_us

import urandom
from machine import UART, Pin

from shared.config import DMX_BAUDRATE, DMX_TX_ENABLE_PIN, DMX_TX_PIN

UART_ID = 1
FRAME_DELAY_MS = 15
STOP_POLL_MS = 10


tx_enable = Pin(DMX_TX_ENABLE_PIN, Pin.OUT)


def set_transmit_enabled(enabled):
    tx_enable.value(1 if enabled else 0)


tx = Pin(DMX_TX_PIN)
uart = UART(
    UART_ID,
    baudrate=DMX_BAUDRATE,
    bits=8,
    parity=None,
    stop=2,
    tx=tx,
)

_tx_lock = _thread.allocate_lock()
_state_lock = _thread.allocate_lock()
_worker_active = False
_stop_requested = False


def send_dmx_frame(red, green, blue):
    frame = bytes((0, red, green, blue))
    _tx_lock.acquire()
    try:
        set_transmit_enabled(True)
        try:
            uart.init(baudrate=9600, bits=8, parity=None, stop=2, tx=tx)
            uart.write(b"\x00")
            sleep_us(1300)

            uart.init(baudrate=DMX_BAUDRATE, bits=8, parity=None, stop=2, tx=tx)
            uart.write(frame)
            sleep_us(len(frame) * 44)
        finally:
            ...
            # set_transmit_enabled(False)
    finally:
        _tx_lock.release()


def _should_stop():
    _state_lock.acquire()
    try:
        return _stop_requested
    finally:
        _state_lock.release()


def _pause(ms):
    while ms > 0 and not _should_stop():
        interval = min(ms, STOP_POLL_MS)
        sleep_ms(interval)
        ms -= interval
    return not _should_stop()


def effect_fade(colors, steps=256, delay_ms=FRAME_DELAY_MS):
    """Fade smoothly between the colors, then loop back to the first."""
    for start, end in zip(colors, colors[1:] + colors[:1]):
        for step in range(steps):
            color = tuple(
                start[channel] + (end[channel] - start[channel]) * step // (steps - 1)
                for channel in range(3)
            )
            send_dmx_frame(*color)
            if not _pause(delay_ms):
                return


def effect_color_hold(colors, hold_ms=700):
    """Show each color at full intensity for a fixed interval."""
    for color in colors:
        send_dmx_frame(*color)
        if not _pause(hold_ms):
            return


def effect_pulse(color, steps=100, delay_ms=10):
    """Fade one color up to full brightness and back down."""
    for brightness in range(steps + 1):
        level = brightness * 255 // steps
        send_dmx_frame(*(channel * level // 255 for channel in color))
        if not _pause(delay_ms):
            return

    for brightness in range(steps - 1, -1, -1):
        level = brightness * 255 // steps
        send_dmx_frame(*(channel * level // 255 for channel in color))
        if not _pause(delay_ms):
            return


def effect_random_colors(count=20, hold_ms=350):
    """Jump between randomly chosen RGB colors."""
    for _ in range(count):
        color = tuple(urandom.getrandbits(8) for _ in range(3))
        send_dmx_frame(*color)
        if not _pause(hold_ms):
            return


def fixed_colors(r, g, b):
    """Show a fixed RGB color."""
    send_dmx_frame(r, g, b)


palette = (
    (255, 0, 0),
    (255, 96, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 255),
    (0, 0, 255),
    (160, 0, 255),
)


def _demo_worker():
    global _worker_active
    try:
        while not _should_stop():
            effect_fade(palette)
            effect_color_hold(((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)))
            effect_pulse((255, 40, 0))
            effect_random_colors()
    finally:
        _tx_lock.acquire()
        try:
            # set_transmit_enabled(False)
            ...
        finally:
            _tx_lock.release()

        _state_lock.acquire()
        try:
            _worker_active = False
        finally:
            _state_lock.release()


def start_demo():
    """Start the looping effects in a background MicroPython thread."""
    global _worker_active, _stop_requested
    _state_lock.acquire()
    try:
        if _worker_active:
            return False
        _worker_active = True
        _stop_requested = False
    finally:
        _state_lock.release()

    try:
        _thread.start_new_thread(_demo_worker, ())
    except Exception:
        _state_lock.acquire()
        try:
            _worker_active = False
        finally:
            _state_lock.release()
        raise
    return True


def stop_demo():
    """Request shutdown and wait for the worker to finish its current DMX frame."""
    global _stop_requested
    _state_lock.acquire()
    try:
        _stop_requested = True
    finally:
        _state_lock.release()

    while True:
        _state_lock.acquire()
        try:
            active = _worker_active
        finally:
            _state_lock.release()
        if not active:
            return
        sleep_ms(STOP_POLL_MS)
