# All tunables for the DMX stage-prop rotator (ESP32-S3).

# ---- Pins (avoid GPIO26-37 on N16R8 = flash/PSRAM, and strapping pins 0/3/45/46) ----
DMX_RX_PIN = 15  # MAX485 RO -> (level shift to 3.3V if MAX485 runs at 5V)
STEP_PIN = 12  # TB6600 PUL+
DIR_PIN = 14  # TB6600 DIR+
ENABLE_PIN = None  # TB6600 ENA+ (None if unused)
LIMIT_PIN = None  # limit / hall sensor input
LED_PIN = None  # optional status LED (plain GPIO)

# ---- Input source ----
INPUT = "webrepl"  # "webrepl" | "dmx" | "ir"  (only the selected one is initialised)
RUN_MODE = (
    "thread"  # "thread" (2nd thread, REPL stays free) | "timer" (soft Timer fallback)
)
REPL_WATCHDOG_S = None  # webrepl: stop if no command for this long (None = never)
IR_PIN = None

# ---- DMX (only used when INPUT = "dmx") ----
DMX_UART_ID = 1
DMX_ADDRESS = 1  # start address (1-512)
DMX_TIMEOUT_MS = 5000  # no valid frame for this long => decelerate to stop
DMX_BREAK_MIN_US = (
    60  # low pulse longer than this is a BREAK (data bytes are <= 36us low)
)
DMX_LEADING_SKIP = (
    0  # set to 1 if the UART delivers the BREAK as an extra 0x00 byte at frame start
)

# Channel offsets from DMX_ADDRESS (footprint = 4)
CH_MODE = 0  # 0-63 stop, 64-127 speed, 128-191 position, 192-255 home/zero
CH_VALUE = 1  # speed: 0-127 CCW, 128 stop, 129-255 CW | position: coarse 16-bit
CH_FINE = 2  # position fine byte
CH_LIMIT = (
    3  # speed limit for position mode & speed mode (0 = 100%, else 1-255 -> ~0.4-100%)
)

# ---- Mechanics ----
MOTOR_FULL_STEPS = 200  # NEMA17 1.8 deg
MICROSTEPS = 16  # must match TB6600 DIP switches
DRIVE_TEETH = 20
DRIVEN_TEETH = 60
MICROSTEPS_REV = MOTOR_FULL_STEPS * MICROSTEPS  # steps per motor rev (used by stepper_1)
GEARBOX_MODIFIER = DRIVEN_TEETH / DRIVE_TEETH  # motor revs per prop rev (3x) (used by stepper_1)
INVERT_DIR = False  # (used by stepper_1)
PROP_STEPS_PER_REV = MICROSTEPS_REV * GEARBOX_MODIFIER

# ---- Motion (stepper_1 runs at a constant speed, no ramps) ----
MAX_SPEED_RPM = 30.0  # prop RPM at full speed
SPEED_SPS = round(MAX_SPEED_RPM / 60.0 * PROP_STEPS_PER_REV)  # steps/s at full speed (used by stepper_1)
MIN_STEP_HZ = 50  # speeds below this are treated as stop
STEP_TIMER_ID = -1  # machine.Timer id passed to stepper_1 (-1 = virtual timer)
POSITION_SHORTEST_PATH = (
    False  # True: position mode wraps and takes the shortest way round
)

# ---- Driver enable (stepper_1 drives ENABLE_PIN high when enabled) ----
DISABLE_AFTER_IDLE_S = (
    None  # e.g. 10 to release the motor after this long stopped; None = hold
)

# ---- Limit / hall switch ----
LIMIT_ENABLED = False
LIMIT_ACTIVE_LEVEL = 0  # pin level when triggered
LIMIT_PULL_UP = True
HOME_DIRECTION = -1  # +1 / -1 direction of travel to find the switch
HOME_SPEED_RPM = 5.0
HOME_OFFSET_DEG = 0.0  # prop angle of the switch position
REQUIRE_HOMED = False  # refuse position mode until homed

# ---- Misc ----
CONTROL_PERIOD_MS = 10
LOG_AUTO = False           # True: log automatically (only when valid/mode/homed change). False: opt-in via log() / status()

WIFI_TIMEOUT_SECONDS = 20
