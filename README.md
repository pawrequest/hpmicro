# DMX stage-prop rotator (ESP32-S3 + MAX485 + TB6600)

MicroPython. Copy the contents of `src/` (including `inputs/`) to the board root.
Host tests: `.venv\Scripts\python.exe -m unittest discover -s tests`.

## Design
One input source is selected with `INPUT` in `src/config.py` (`"webrepl"`, `"dmx"` or `"ir"`); only that one is
initialised, so DMX hardware is untouched unless chosen.
- `src/command.py`: shared desired state (mode/speed/position/limit/valid). Inputs write it, `Prop` reads it.
- `src/inputs/`: `dmx_input.py` (channel map), `repl_input.py` (REPL API), `ir_input.py` (stub).
- `src/dmx.py`: UART1 250000 8N2 + hard pin IRQ on the RX line detecting BREAK; `service()` splits the byte stream at
  exact break positions and publishes the latest frame.
- `src/stepper_1.py`: known-good driver (micropython-stepper): a Timer callback emits steps and keeps an exact step count. Unmodified.
- `src/stepper.py`: thin adapter over stepper_1; stops its timer when idle and only re-inits the timer when speed/direction/target really change (re-initialising it repeatedly made motion jerky).
- `src/prop.py`: constant-speed motion (no ramps), homing, stop-on-invalid-input. Runs at 100 Hz.
- `src/main.py`: runs the control loop in a second thread (`RUN_MODE="thread"`) so the REPL/WebREPL stays free;
  `RUN_MODE="timer"` uses a soft Timer instead if threads misbehave. REPL globals: `ctl`, `inp`, `prop`, `stepper`, `start()`, `stop()`, `status()`, `log()`.

## WebREPL control (`INPUT = "webrepl"`)
```python
ctl.speed(0.5)  # -1..1 of max speed
ctl.rpm(10)  # prop RPM
ctl.goto(90)  # prop angle, degrees
ctl.home()  # zero / find limit switch
ctl.limit(50)  # cap speed at 50 %
ctl.stop()  # decelerate and hold
ctl.status()
stop()  # end control loop, disable driver (start() to resume)
```
`REPL_WATCHDOG_S` can stop the motor if no command arrives for N seconds (default off).

## Logging
No periodic output (it garbles the terminal). `status()` prints the current state once; `log()` / `log(False)` toggles
logging at runtime. Logging only prints when `valid`, mode or `homed` changes. `LOG_AUTO = True` in `config.py`
enables it from boot.

## Wiring
- MAX485: A/B to DMX pins 3(+)/2(-), RO -> GPIO18 (**3.3 V max** - use a divider/level shifter or a 3.3 V MAX3485),
  DE and /RE tied to GND (receive only). Use a 120 ohm terminator if last in line.
- TB6600: PUL+/DIR+/ENA+ to GPIO4/5/6, the minus inputs to GND. The optocoupler inputs are specified for 5 V;
  if the motor misbehaves at 3.3 V adjust the series resistor or buffer with a transistor/level shifter.
  stepper_1 drives ENA high when enabled (ENABLE_PIN is None by default).
- Set TB6600 microstep DIP switches to match `MICROSTEPS`, and current for your NEMA17.
- Optional limit/hall: `LIMIT_ENABLED = True`, pin/polarity in `src/config.py`.

## DMX channels (`INPUT = "dmx"`, start at `DMX_ADDRESS`)
| Ch | Function |
|----|----------|
| 1 | Mode: 0-63 stop, 64-127 speed, 128-191 position, 192-255 home (zero) |
| 2 | Speed mode: 0-127 CCW, 128 stop, 129-255 CW. Position mode: coarse angle |
| 3 | Position fine byte (16-bit angle 0-360 deg of the prop) |
| 4 | Speed limit (0 = 100%) |

Loss of DMX for `DMX_TIMEOUT_MS`: decelerate to a stop. No motion until the first valid frame.

## Bring-up notes (untested on hardware)
- Watch the periodic log (`frames`, `bad`) over serial/WebREPL. If `bad` climbs and `frames` stays 0 the UART likely
  delivers the BREAK as an extra 0x00 byte: set `DMX_LEADING_SKIP = 1`.
- If `uart.any()` is not permitted in a hard IRQ on your firmware, switch `hard=True` to `False` in `src/dmx.py`.
- Position is open-loop (step counting); home to re-reference.
