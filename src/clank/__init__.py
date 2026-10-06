"""clank: DMX laptop -> ESP32 control link.

protocol.py  shared channel map (deploy to both sides)
host.py      laptop only: typed Command <-> frame
device.py    ESP32 only: State decoder + failsafe (deploy with protocol.py)
"""
