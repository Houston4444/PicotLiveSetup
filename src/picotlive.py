from enum import Enum, IntFlag
from random import random


from mentat import Engine
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from main_engine import MainEngine


engine = MainEngine('ElMentator', 4687, 'folodermmentata')
midi_module = Leonardo('pedalboard', protocol="midi")
sooperlooper = SooperLooper('sooperlooper', protocol="osc", port=9951)
seq192 = Seq192()
random_listener = RandomListener('randomSeq')
engine.add_module(midi_module)
engine.add_module(sooperlooper)
engine.add_module(seq192)
engine.add_module(random_listener)
engine.add_main_route()

engine.autorestart()
engine.start()