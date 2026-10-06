import time

from shared.config import DIR_PIN, MAX_SPEED_SPS, MICROSTEPS_REV, STEP_PIN
from stepper_redox import StepperRedox


def get_step() -> StepperRedox:
    print(
        f"creating stepper with: step_pin={STEP_PIN}, dir_pin={DIR_PIN}, steps/rev={MICROSTEPS_REV}, speed sps={MAX_SPEED_SPS}"
    )
    st = StepperRedox(
        step_pin=STEP_PIN,
        dir_pin=DIR_PIN,
        steps_per_rev=MICROSTEPS_REV,
        speed_sps=MAX_SPEED_SPS,
    )
    return st


def print_pos(st):
    print(st.get_pos(), st.get_pos_deg(), st.get_pos_rad())


def for_3_seconds(st):
    st.free_run(1)
    time.sleep(3)
    st.stop()


def do_it():
    print("doing it")
    st = get_step()
    print_pos(st)

    print(f"rotating {30} degrees")
    st.target_deg(30)


st = get_step()
print_pos(st)


def on_button_press():
    print("button pressed")
    print(f"rotating {90} degrees")
    st.target_deg(st.get_pos_deg() + 90)

# button = Button(on_button_press)
