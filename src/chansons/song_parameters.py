from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional


if TYPE_CHECKING:
    from main_engine import MainEngine
    from leonardo import FsButton

REPETTE = True

def scene_method():
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            song: SongParameters = args[0]
            ret = func(*args, **kwargs)
            if song.scenes:
                song._current_scene = (
                    (song._current_scene + 1) % len(song.scenes))
            
            if REPETTE:
                if not song._repette_started and len(song.scenes) > 1:
                    scene = song.scenes[song._current_scene]
                    song.engine.start_scene(
                        f'{song.__repr__()}_{scene.__name__}', scene)
            return ret
        return wrapper
    return decorator


class Marker(Enum):
    ...


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
    kick_velo_ratio = 1.0
    drum_velocity = 100.0
    
    def __init__(self):
        self._repette_started = False
        self._scene_running = False
        self._loop_louped = False
        self.engine: Optional[MainEngine] = None
        self.scenes = list[Callable]()
        self._current_scene = 0
        self._current_marker: Optional[Marker] = None

    def __repr__(self) -> str:
        return self.__class__.__name__
    
    def set_engine(self, engine: 'MainEngine'):
        self.engine = engine
    
    def wait(self, *args):
        if REPETTE and not self._repette_started:
            return
        self.engine.wait(*args)
    
    def start_main_scene(self, engine: 'MainEngine'):
        self.engine = engine
        
        if self._scene_running:
            return
        
        if not self.scenes:
            print('Y a pas de scenes dans ta chanson !!!')
            return
        
        self._scene_running = True
        
        scene = self.scenes[self._current_scene]
        print('hopeula', self.__repr__(), self._current_scene)

        engine.start_scene(
            f'{self.__repr__()}_{self._current_scene}', scene)

    def stop_main_scene(self):
        if not self._scene_running:
            return
        
        self._scene_running = False
        
        if self.engine is None:
            return
        
        if not self.scenes:
            return
        
        scene = self.scenes[self._current_scene]

        self.engine.modules['sooperlooper'].mute_all()
        self.engine.stop_scene(f'{self.__repr__()}_{self._current_scene}')

    @scene_method()
    def main_scene(self):
        '''scene method'''
        ...

    def set_loop_looped(self):
        self._loop_louped = True
        
    def vfs5_event(self, fsb: 'FsButton', fs_on: bool):
        ...
        
    def trigger_event(self):
        ...
        
    def loop_len_recv(self, loop_len: float):
        ...