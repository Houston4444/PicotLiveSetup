
import signal
import os
import logging

from non_multip import NonXtMultip
from non_arch_delay import NonXtArchDelay
from impact import Impact
from leonardo import Leonardo
from random_listener import RandomListener
from sooperlooper import SooperLooper
from seq192 import Seq192
from ardour import Ardour
from carla import Carla
from songs import SONGS
from nsm_mentator import NsmMentator, OptionalGui
from main_engine import MainEngine

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

# def signal_handler(sig, frame):
#     print('zeofkappo', sig, frame)


engine = MainEngine('ElMentator', 4687, 'folodermmentata', tcp_port=4484)

for module in (
        Leonardo('pedalboard', protocol="midi"),
        SooperLooper('sooperlooper', protocol="osc", port=9951),
        NonXtMultip('non_xt_multip', protocol="osc", port=7787),
        NonXtArchDelay('non_xt_archdelay', protocol="osc", port=7788),
        Seq192(),
        Impact(),
        Ardour('ardour', protocol="osc", port=3819),
        Carla('carla', protocol="osc.tcp", port=19998),
        RandomListener('randomSeq')): 
    engine.add_module(module)

if os.getenv('NSM_URL'):
    engine.add_module(NsmMentator())
    engine.add_module(OptionalGui())

engine.add_main_route()

engine.set_song(SONGS[0])
engine.autorestart()

# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)
# engine.modules['seq192'].start()


engine.start()

engine.modules['carla'].stop_osc_tcp()