class Command:
    """Shared desired state. Written by the active input, read by Prop."""

    def __init__(self):
        self.valid = False  # False => source absent/lost, motor decelerates to stop
        self.mode = "stop"  # stop | speed | position | home
        self.speed = 0.0  # -1..1 of max speed (speed mode)
        self.position_deg = 0.0  # prop angle (position mode)
        self.limit = 1.0  # (0..1] fraction of max speed
