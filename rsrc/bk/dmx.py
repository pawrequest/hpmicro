"""DMX512 receiver for ESP32 MicroPython (MAX485 RO -> UART RX).

Frame sync: a hard pin IRQ on the RX line measures the low time. A low longer than
DMX_BREAK_MIN_US is a BREAK; at its end we record the absolute stream position
(bytes consumed + bytes waiting in the UART buffer). service() splits the
byte stream at those positions, so alignment is exact regardless of task latency.
"""

from time import ticks_diff, ticks_ms, ticks_us

import config
from machine import UART, Pin

_MASK = 0xFFFFFF
_HALF = 0x800000


class DMXReceiver:
    def __init__(self):
        rx = config.DMX_RX_PIN
        self._pin = Pin(rx, Pin.IN)
        self.uart = UART(
            config.DMX_UART_ID,
            baudrate=250000,
            bits=8,
            parity=None,
            stop=2,
            rx=rx,
            rxbuf=2048,
            timeout=0,
        )
        self._chunk = bytearray(256)
        self._chunk_mv = memoryview(self._chunk)
        self._acc = bytearray(520)
        self._acc_mv = memoryview(self._acc)
        self._n = 0
        self._synced = False
        self.slots = bytearray(512)
        self.slots_len = 0
        self.frames = 0
        self.bad_frames = 0
        self.last_ms = ticks_ms()
        self._consumed = 0
        self._bpos = [0, 0, 0, 0]
        self._bn = 0
        self._seen = 0
        self._fall = 0
        self._break_min = config.DMX_BREAK_MIN_US
        self._skip = config.DMX_LEADING_SKIP
        self._pin.irq(self._edge, Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

    def _edge(self, pin):
        now = ticks_us()
        if pin.value() == 0:
            self._fall = now
        elif ticks_diff(now, self._fall) >= self._break_min:
            self._bpos[self._bn & 3] = (self._consumed + self.uart.any()) & _MASK
            self._bn += 1

    def _append(self, off, m):
        if not self._synced or m <= 0:
            return
        room = 513 + self._skip - self._n
        m = min(m, room)
        if m > 0:
            self._acc_mv[self._n : self._n + m] = self._chunk_mv[off : off + m]
            self._n += m

    def _finish_frame(self):
        n = self._n - self._skip
        if self._synced and n >= 1:
            if self._acc[self._skip] == 0:
                cnt = n - 1
                self.slots_len = cnt
                self.slots[0:cnt] = self._acc_mv[self._skip + 1 : self._skip + n]
                self.frames += 1
                self.last_ms = ticks_ms()
            else:
                self.bad_frames += 1  # non-zero start code (RDM etc.) or misaligned
        self._synced = True
        self._n = 0

    def _consume(self, n):
        pos = self._consumed
        i = 0
        while i < n:
            if self._seen != self._bn:
                rel = (self._bpos[self._seen & 3] - pos) & _MASK
                if rel >= _HALF:
                    rel = 0
                if rel <= n - i:
                    self._append(i, rel)
                    self._finish_frame()
                    self._seen += 1
                    i += rel
                    pos = (pos + rel) & _MASK
                    continue
            self._append(i, n - i)
            pos = (pos + n - i) & _MASK
            break
        self._consumed = (self._consumed + n) & _MASK

    def service(self):
        """Drain the UART buffer; call at least every ~20 ms."""
        while True:
            n = self.uart.readinto(self._chunk)
            if not n:
                return
            self._consume(n)
            if n < len(self._chunk):
                return

    def signal_ok(self):
        return self.frames > 0 and ticks_diff(ticks_ms(), self.last_ms) < config.DMX_TIMEOUT_MS

    def channel(self, offset):
        i = config.DMX_ADDRESS - 1 + offset
        return self.slots[i] if 0 <= i < self.slots_len else 0
