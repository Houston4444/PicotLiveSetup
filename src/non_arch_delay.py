
from typing import TYPE_CHECKING, Union
from rmodule import RModule
from enum import IntEnum

from songs import SongParameters

if TYPE_CHECKING:
    from main_engine import MainEngine

class Param(IntEnum):
    KICK_SPACING = 0
    OPEN_TIME = 1
    KICK_SNARE_DEMUTE = 2


OSC_SYMBOL_DICT = {
    Param.KICK_SPACING: 'double_kick_spacing',
    Param.OPEN_TIME: 'open_time',
    Param.KICK_SNARE_DEMUTE: 'ks_demute'
}



class NonXtArchDelay(RModule):    
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        self.params = dict[SongParameters, dict[str, float]]()
        self._all_paths = set[str]()

    def _send_pg(self, param: Param, value: Union[str, bool, int, float]):
        self.send(
            '/Non-Mixer-XT.archdelay/strip/delay/Delay%20Architect/'
            f'{OSC_SYMBOL_DICT[param]}/unscaled', float(value))

    def set_song(self, song: SongParameters):
        # beat_duration = 1000 * 60 / song.average_tempo
        # print('SOijef set song', beat_duration, beat_duration * song.kick_spacing_beats, beat_duration * song.open_time_beats)
        # self._send_pg(Param.KICK_SPACING, beat_duration * song.kick_spacing_beats)
        # self._send_pg(Param.OPEN_TIME, beat_duration * song.open_time_beats)
        # self._send_pg(Param.KICK_SNARE_DEMUTE, int(song.kick_snare_demute))
        url = f"osc.udp://houstonbureau:{self.engine.port}/"
        print('mmqq', self.name, url)
        self.send('/signal/hello', self.name, url)
        
        self.send('/signal/list')
        
    def route(self, address: str, args: list):
        # print('lls', address, args)
        if address != '/reply':
            print('ziji', address, args)
            return
        
        if len(args) != 6:
            print('pamls', address, args)
            if len(args) == 1 and args[0] == '/signal/list':
                print('connect all')
                self.connect_all()
            return
        
        signal_path, path, direction, min, max, default = args
        
        if signal_path != '/signal/list':
            print('chcaoo', args)
            return
        
        path: str
        direction: str
        min: float
        max: float
        default: float
        
        if path.endswith('/unscaled'):
            return
        
        if direction == 'out':
            return
        
        # print('zaza', address, args)
        short_path = path.rpartition('/')[2]
        print('slip', short_path, default)
        # dicti = self.params.get(self.engine)
        # self.send('/signal/connect', '/marrata', path)
        self._all_paths.add(path)
        
    def connect_all(self):
        # return
        
        for path in self._all_paths:
            # print('prala', path)
            self.send('/signal/connect', '/maleeed', path)