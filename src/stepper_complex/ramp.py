"""Pure motion/mapping maths (runs on host for tests)."""

from math import sqrt


def slew(cur, tgt, accel, dt):
    """Move cur toward tgt by at most accel*dt."""
    step = accel * dt
    d = tgt - cur
    if d > step:
        return cur + step
    if d < -step:
        return cur - step
    return tgt


def approach_velocity(remaining, vmax, accel):
    """Signed velocity that lets us brake to a stop exactly at the target."""
    mag = sqrt(2.0 * accel * 0.9 * abs(remaining))
    mag = min(mag, vmax)
    return mag if remaining >= 0 else -mag


def mode_from_dmx(v):
    if v < 64:
        return "stop"
    if v < 128:
        return "speed"
    if v < 192:
        return "position"
    return "home"


def speed_fraction(v):
    """DMX 0-255 -> -1..1 (128 = stop)."""
    if v == 128:
        return 0.0
    if v > 128:
        return (v - 128) / 127.0
    return -(128 - v) / 128.0


def limit_fraction(v):
    return 1.0 if v == 0 else v / 255.0


def position_fraction(coarse, fine):
    return ((coarse << 8) | fine) / 65535.0


def shortest_delta(target, current, rev):
    """Signed distance target-current wrapped into [-rev/2, rev/2]."""
    d = (target - current) % rev
    if d > rev / 2:
        d -= rev
    return d
