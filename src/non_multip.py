
from typing import Union
from rmodule import RModule
from enum import IntEnum

from songs import SongParameters
    

class Param(IntEnum):
    KICK_SPACING = 0
    OPEN_TIME = 1
    KICK_SNARE_DEMUTE = 2
    KICK_VELO_RATIO = 3
    VELOCITY = 4


OSC_SYMBOL_DICT = {
    Param.KICK_SPACING: 'double_kick_spacing',
    Param.OPEN_TIME: 'open_time',
    Param.KICK_SNARE_DEMUTE: 'ks_demute',
    Param.KICK_VELO_RATIO: 'kick_velocity_ratio',
    Param.VELOCITY: 'velocity'
}



class NonXtMultip(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        for param in Param:
            self.add_parameter(
                param.name,
                '/Non-Mixer-XT.m_xt/strip/multip/Plujain-Multipmidi/'
                    f'{OSC_SYMBOL_DICT[param]}/unscaled',
                'f',
                default=1.0 if param is Param.KICK_SNARE_DEMUTE else 100.0
                )

    def _send_pg(self, param: Param, value: Union[str, bool, int, float]):
        self.send(
            '/Non-Mixer-XT.m_xt/strip/multip/Plujain-Multipmidi/'
            f'{OSC_SYMBOL_DICT[param]}/unscaled', float(value))

    def set_song(self, song: SongParameters):
        beat_duration = 1000 * 60 / song.average_tempo
        
        self.set(Param.KICK_SPACING.name,
                 beat_duration * song.kick_spacing_beats)
        self.set(Param.OPEN_TIME.name, beat_duration * song.open_time_beats)
        self.set(Param.KICK_SNARE_DEMUTE.name, int(song.kick_snare_demute))
        self.set(Param.KICK_VELO_RATIO.name, song.kick_velo_ratio)
        self.set(Param.VELOCITY.name, song.drum_velocity)
        
    def set_velocity(self, velocity: float):
        self.set(Param.VELOCITY.name, velocity)
        
    def animate_velocity(self, start: float, end: float, duration: float):
        self.animate(Param.VELOCITY.name, start, end, duration, 'beats')