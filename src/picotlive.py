
import signal

from non_multip import NonXtMultip
from impact import Impact
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from ardour import Ardour
from songs import SongParameters, Avale
from nsm import NsmClient
from main_engine import MainEngine

def signal_handler(sig, frame):
    print('zeofk', sig, frame)


engine = MainEngine('ElMentator', 4687, 'folodermmentata')

for module in (
        Leonardo('pedalboard', protocol="midi"),
        SooperLooper('sooperlooper', protocol="osc", port=9951),
        NonXtMultip('non_xt_multip', protocol="osc", port=7787),
        Seq192(),
        Impact(),
        Ardour('ardour', protocol="osc", port=3819),
        RandomListener('randomSeq'),
        NsmClient()):
    engine.add_module(module)

engine.add_main_route()

engine.set_song(Avale())
engine.autorestart()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

engine.start()