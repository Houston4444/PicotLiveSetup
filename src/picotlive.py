
from carla_multip import CarlaMultip
from impact import Impact
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from songs import SongParameters, Avale
from main_engine import MainEngine


engine = MainEngine('ElMentator', 4687, 'folodermmentata')
# midi_module = Leonardo('pedalboard', protocol="midi")
# sooperlooper = SooperLooper('sooperlooper', protocol="osc", port=9951)
# carla_multip = CarlaMultip('carla_multip', protocol="osc", port=9986)
# seq192 = Seq192()
# random_listener = RandomListener('randomSeq')
# impact = Impact()
# engine.add_module(midi_module)
# engine.add_module(sooperlooper)
# engine.add_module(carla_multip)
# engine.add_module(seq192)
# engine.add_module(random_listener)
# engine.add_module(impact)

for module in (
        Leonardo('pedalboard', protocol="midi"),
        SooperLooper('sooperlooper', protocol="osc", port=9951),
        CarlaMultip('carla_multip', protocol="osc", port=9986),
        Seq192(),
        Impact(),
        RandomListener('randomSeq')):
    engine.add_module(module)

engine.add_main_route()

engine.set_song(Avale())
engine.autorestart()
engine.start()