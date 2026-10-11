from esp_rx.inputs.base import Input

from esp_rx import config, ramp


class DmxInput(Input):
    def __init__(self, cmd, dmx=None):
        Input.__init__(self, cmd)
        if dmx is None:
            from esp_rx.dmx import DMXReceiver  # only imported when DMX is selected

            dmx = DMXReceiver()
        self.dmx = dmx

    def poll(self):
        d = self.dmx
        c = self.cmd
        d.service()
        if not d.signal_ok():
            c.valid = False
            return
        value = d.channel(config.CH_VALUE)
        c.mode = ramp.mode_from_dmx(d.channel(config.CH_MODE))
        c.speed = ramp.speed_fraction(value)
        c.position_deg = (
            ramp.position_fraction(value, d.channel(config.CH_FINE)) * 360.0
        )
        c.limit = ramp.limit_fraction(d.channel(config.CH_LIMIT))
        c.valid = True
