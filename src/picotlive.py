from enum import Enum, IntFlag

import sys
from pathlib import Path

from mentat import Engine, Module
from leonardo import Leonardo
from sooperlooper import SooperLooper
from seq192 import Seq192
    
class MainEngine(Engine):
    def __init__(self, name, port, folder, debug=False, tcp_port=None, unix_port=None):
        super().__init__(name, port, folder, debug, tcp_port, unix_port)


engine = MainEngine('ElMentator', 4687, 'folodermmentata')
midi_module = Leonardo('pedalboard', protocol="midi")
sooperlooper = SooperLooper('sooperlooper', protocol="osc", port=9951)
seq192 = Seq192()
engine.add_module(midi_module)
engine.add_module(sooperlooper)
engine.add_module(seq192)

engine.autorestart()
engine.start()