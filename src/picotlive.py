from enum import Enum, IntFlag
from random import random


from mentat import Engine
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from routinette import Routinette
    
class MainEngine(Engine):
    def __init__(self, name, port, folder, debug=False, tcp_port=None, unix_port=None):
        super().__init__(name, port, folder, debug, tcp_port, unix_port)


engine = MainEngine('ElMentator', 4687, 'folodermmentata')
midi_module = Leonardo('pedalboard', protocol="midi")
sooperlooper = SooperLooper('sooperlooper', protocol="osc", port=9951)
routinette = Routinette('routinette')
seq192 = Seq192(routinette)
random_listener = RandomListener('randomSeq')
engine.add_module(midi_module)
engine.add_module(sooperlooper)
engine.add_module(seq192)
engine.add_module(random_listener)
engine.add_route(routinette)

engine.autorestart()
engine.start()