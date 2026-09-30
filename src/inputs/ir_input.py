from inputs.base import Input

# TODO: IR remote. Planned: config.IR_PIN, a key map such as
#   {KEY_LEFT: ("speed", -0.3), KEY_RIGHT: ("speed", 0.3), KEY_OK: ("stop", 0), KEY_HOME: ("home", 0)}
# decoded in an IRQ and applied to self.cmd (set cmd.valid = True on any key press).


class IrInput(Input):
    def __init__(self, cmd):
        Input.__init__(self, cmd)
        print("IR input not implemented yet: motor stays idle")
