class Input:
    """Base class for command sources. poll() is called every control tick."""

    def __init__(self, cmd):
        self.cmd = cmd

    def poll(self):
        pass
