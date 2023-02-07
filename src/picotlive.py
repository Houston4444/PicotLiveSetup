
from carla_multip import CarlaMultip
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192, SongParameters
from main_engine import MainEngine


engine = MainEngine('ElMentator', 4687, 'folodermmentata')
midi_module = Leonardo('pedalboard', protocol="midi")
sooperlooper = SooperLooper('sooperlooper', protocol="osc", port=9951)
carla_multip = CarlaMultip('carla_multip', protocol="osc", port=9986)
seq192 = Seq192()
random_listener = RandomListener('randomSeq')
engine.add_module(midi_module)
engine.add_module(sooperlooper)
engine.add_module(carla_multip)
engine.add_module(seq192)
engine.add_module(random_listener)
engine.add_main_route()

seq192.change_song(SongParameters())
engine.autorestart()
engine.start()