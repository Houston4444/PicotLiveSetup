from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main_engine import MainEngine


class SongParameters:
    # le seq192 de base
    ardour_scene = 0
    seq_page = 0
    stop_time = 2.500 # en secondes
    average_tempo = 92.0
    taps_for_tempo = 1
    tempo_style = ''
    vox_program = ''

    kick_restarts_cycle = False
    restart_precision: 1.0 # en beats
    restart_acceptability = 0.4 # from 0.0 to 1.0
    tempo_animation_unit = 0.5 # en beats
    tempo_animation_len = 6
    tempo_factor = 0.5
    moving_tempo = 0.00 # en pourcents

    immediate_sequence_switch = False
    
    # le seq192 impact
    impact_col = 0
    
    kick_spacing = 100 # en ms
    kick_spacing_beats = 1/4
    open_time_beats = 1/4
    kick_snare_demute = True
    
    def __init__(self):
        self._main_scene_running = False
        self._loop_louped = False
        self.engine: Optional[MainEngine] = None 

    def __repr__(self) -> str:
        return self.__class__.__name__
    
    def start_main_scene(self, engine: 'MainEngine'):
        self.engine = engine
        
        if self._main_scene_running:
            return
        
        self._main_scene_running = True
        engine.start_scene(f'{self.__repr__()}_main', self.main_scene)

    def stop_main_scene(self):
        if not self._main_scene_running:
            return
        
        self._main_scene_running = False
        
        if self.engine is None:
            return
        
        self.engine.modules['sooperlooper'].mute_all()
        self.engine.stop_scene(f'{self.__repr__()}_main')

    def main_scene(self):
        '''scene method'''
        ...

    def set_loop_looped(self):
        self._loop_louped = True