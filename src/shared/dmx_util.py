"""The robot's DMX channel layout. The only file to edit when channels change.

Channel table (offsets relative to the device's DMX start address) is derived from
LAYOUT below; see shared/dmx_layout.py for the available kinds.
"""

from shared.dmx_layout import Enum, Layout, Level, U8

# CH_MODE values (spaced apart so small DMX jitter can't flip a mode)
MODE_STOP = 0
MODE_RUN = 100

LAYOUT = Layout(
    [
        ('mode', Enum((MODE_STOP, MODE_RUN), MODE_STOP)),
        ('level', Level()),  # master brightness
        ('r', U8()),
        ('g', U8()),
        ('b', U8()),
    ]
)
FOOTPRINT = LAYOUT.footprint
