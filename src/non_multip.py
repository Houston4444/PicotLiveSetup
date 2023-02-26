
from typing import Union
from mentat import Module
from enum import IntEnum

from songs import SongParameters
    

class Param(IntEnum):
    KICK_SPACING = 0
    OPEN_TIME = 1
    KICK_SNARE_DEMUTE = 2


OSC_SYMBOL_DICT = {
    Param.KICK_SPACING: 'double_kick_spacing',
    Param.OPEN_TIME: 'open_time',
    Param.KICK_SNARE_DEMUTE: 'ks_demute'
}


class NonXtMultip(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)

    def _send_pg(self, param: Param, value: Union[str, bool, int, float]):
        self.send(
            'Non-Mixer-XT.m_xt/strip/multip/Plujain-Multipmidi/'
            f'{OSC_SYMBOL_DICT[param]}/unscaled', float(value))

    def set_song(self, song: SongParameters):
        beat_duration = 1000 * 60 / song.average_tempo
        print('SOijef set song', beat_duration, beat_duration * song.kick_spacing_beats, beat_duration * song.open_time_beats)
        self._send_pg(Param.KICK_SPACING, beat_duration * song.kick_spacing_beats)
        self._send_pg(Param.OPEN_TIME, beat_duration * song.open_time_beats)
        self._send_pg(Param.KICK_SNARE_DEMUTE, int(song.kick_snare_demute))