
import signal
import os

from non_multip import NonXtMultip
from non_arch_delay import NonXtArchDelay
from impact import Impact
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from ardour import Ardour
from carla import Carla
from songs import SongParameters, Avale
from nsm_mentator import NsmMentator
from main_engine import MainEngine

def signal_handler(sig, frame):
    print('zeofk', sig, frame)


engine = MainEngine('ElMentator', 4687, 'folodermmentata')

for module in (
        Leonardo('pedalboard', protocol="midi"),
        SooperLooper('sooperlooper', protocol="osc", port=9951),
        NonXtMultip('non_xt_multip', protocol="osc", port=7787),
        NonXtArchDelay('non_xt_archdelay', protocol="osc", port=7788),
        Seq192(),
        Impact(),
        Ardour('ardour', protocol="osc", port=3819),
        Carla('carla', protocol="osc", port=19999),
        RandomListener('randomSeq')):
    engine.add_module(module)

if os.getenv('NSM_URL'):
    engine.add_module(NsmMentator())

engine.add_main_route()

engine.set_song(Avale())
engine.autorestart()

# engine.modules['seq192'].start()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

engine.start()

engine.modules['carla'].unregister()