"""Entry point. Control loop runs in a second thread (or soft Timer) so the REPL stays free.

REPL globals: inp (selected input; `ctl` alias for webrepl), prop, stepper, start(), stop(), status(), log().
"""

import _thread
from machine import Pin
from time import ticks_us, ticks_diff, sleep_ms

import config
from command import Command
from stepper import Stepper
from limit import LimitSwitch
from prop import Prop

cmd = Command()


def _make_input(name):
    if name == "webrepl":
        from inputs.repl_input import ReplInput

        return ReplInput(cmd)
    if name == "dmx":
        from inputs.dmx_input import DmxInput

        return DmxInput(cmd)
    if name == "ir":
        from inputs.ir_input import IrInput

        return IrInput(cmd)
    raise ValueError("config.INPUT must be 'webrepl', 'dmx' or 'ir'")


stepper = Stepper()
prop = Prop(cmd, stepper, LimitSwitch())
inp = _make_input(config.INPUT)
ctl = inp if config.INPUT == "webrepl" else None
if ctl is not None:
    ctl.prop = prop

_led = Pin(config.LED_PIN, Pin.OUT) if config.LED_PIN is not None else None
_st = {"stop": False, "running": False, "last": 0, "n": 0, "logging": config.LOG_AUTO, "seen": None}
_timer = None


def _status_line():
    extra = ""
    dmx = getattr(inp, "dmx", None)
    if dmx is not None:
        extra = " frames=%d bad=%d" % (dmx.frames, dmx.bad_frames)
    return "input=%s valid=%s mode=%s angle=%.1f rate=%d homed=%s%s" % (
        config.INPUT, cmd.valid, prop.mode, prop.angle_deg(), prop.stepper.rate, prop.homed, extra)


def status():
    """Print current state once (pull-style; never interleaves on its own)."""
    print(_status_line())


def log(on=True):
    """Turn change-logging on/off at runtime (prints only when valid/mode/homed change)."""
    _st["logging"] = on
    _st["seen"] = None


def _tick():
    now = ticks_us()
    dt = ticks_diff(now, _st["last"]) / 1e6
    _st["last"] = now
    inp.poll()
    prop.update(dt)
    _st["n"] += 1
    if _led is not None:
        _led.value(1 if cmd.valid else (_st["n"] // 25) & 1)
    if _st["logging"]:
        state = (cmd.valid, prop.mode, prop.homed)
        if state != _st["seen"]:
            _st["seen"] = state
            print(_status_line())


def _safe_stop():
    stepper.stop_now()
    stepper.enable(False)
    _st["running"] = False


def _thread_main():
    _st["last"] = ticks_us()
    try:
        while not _st["stop"]:
            _tick()
            sleep_ms(config.CONTROL_PERIOD_MS)
    finally:
        _safe_stop()


def _timer_cb(t):
    try:
        _tick()
    except BaseException:
        stop()
        raise


def start():
    global _timer
    if _st["running"]:
        return
    _st["stop"] = False
    _st["running"] = True
    _st["last"] = ticks_us()
    if config.RUN_MODE == "timer":
        from machine import Timer

        _timer = Timer(0)
        _timer.init(
            period=config.CONTROL_PERIOD_MS, mode=Timer.PERIODIC, callback=_timer_cb
        )
    else:
        _thread.stack_size(16384)
        _thread.start_new_thread(_thread_main, ())


def stop():
    global _timer
    _st["stop"] = True
    if _timer is not None:
        _timer.deinit()
        _timer = None
        _safe_stop()


# start()
