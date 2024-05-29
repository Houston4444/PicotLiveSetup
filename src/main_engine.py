import json
from typing import TYPE_CHECKING, TypedDict, Union

from mentat import Engine, Route
from non_arch_delay import NonXtArchDelay
from hydrogen import Hydrogen
from non_multip import NonXtMultip
from nsm_mentator import NsmMentator, OptionalGui
from oscitronix import OsciTronix
from random_listener import RandomListener
from rmodule import RModule
from seq192 import Seq192
from impact import Impact
from leonardo import Leonardo, Vfs5Controls
from ardour import Ardour
from songs import SongParameters, SONGS
from carla import Carla
from jack_tempo import JackTempoSetter
from sooperlooper import SooperLooper
from looper_volumes import LoooperVolumes


class ModulesDict(TypedDict):
    seq192: Seq192
    impact: Impact
    pedalboard: Leonardo
    non_xt_multip: NonXtMultip
    non_xt_archdelay: NonXtArchDelay
    ardour: Ardour
    carla: Carla
    nsm_client: NsmMentator
    optional_gui: OptionalGui
    jack_tempo: JackTempoSetter
    hydrogen: Hydrogen
    sooperlooper: SooperLooper
    randomidi: RandomListener
    looper_volumes: LoooperVolumes
    oscitronix: OsciTronix


class MainRoute(Route):
    engine: 'MainEngine'
    
    def __init__(self, name: str):
        super().__init__(name)
        
        self.songs = SONGS
    
    def led_tempo(self):
        leonardo: Leonardo = self.engine.modules['pedalboard']
        while True:
            j = 0
            while j < self.engine.cycle_length:
                leonardo.send('/note_on', 0, 0x24, 127)
                if not j:
                    leonardo.send('/note_on', 0, 0x25, 127)

                self.wait(0.03125, 'beat')
                leonardo.send('/note_off', 0, 0x24)
                if not j:
                    leonardo.send('/note_off', 0, 0x25)
                
                if j + 1 > self.engine.cycle_length:
                    self.wait_next_cycle()
                else:
                    self.wait(0.96875, 'beat')
                
                j += 1
            
    def change_next_signature(self, signature: str):
        self.wait_next_cycle()
        self.engine.set_time_signature(signature)
    
    def count_beats(self):
        self.engine.beats_since_start = 0.0
        
        while self.engine.playing:
            self.wait(1.0, 'beat')
            self.engine.beats_since_start += 1.0
        
        self.engine.beats_since_start = 0.0


class MainEngine(Engine):
    modules: ModulesDict
    
    def __init__(self, name, port, folder, debug=False, tcp_port=None, unix_port=None):
        super().__init__(name, port, folder, debug, tcp_port, unix_port)
        self.playing = False
        self.beats_since_start = 0.0
        
        self._route = MainRoute('routinette')
        self._route.activate()
        
        self._tmp_filename = '.picot_restart.json'
        
        self.song_index = 0
        self.big_sequence = 0
    
    def restart(self):
        tmp_path = self.modules['nsm_client'].client_path / self._tmp_filename
        restart_dict = {
            'song_index': self.song_index,
            'big_sequence': self.big_sequence,
            'arduino_mode': self.modules['pedalboard'].get_vfs5_control_name()
        }

        with open(tmp_path, 'w') as f:
            json.dump(restart_dict, f)
        super().restart()
    
    def start(self):
        tmp_path = self.modules['nsm_client'].client_path / self._tmp_filename
        if tmp_path.exists():
            with open(tmp_path, 'r') as f:
                restart_dict = json.load(f)

            self.set_song(restart_dict['song_index'])
            self.set_big_sequence(restart_dict['big_sequence'])
            self.modules['pedalboard'].change_vfs5_controls(
                Vfs5Controls.from_name(restart_dict['arduino_mode']))
            
            # remove the tmp file
            tmp_path.unlink()
        else:
            self.set_song(0)
            self.set_big_sequence(0)
            self.modules['pedalboard'].change_vfs5_controls(Vfs5Controls.SONG)
        
        super().start()
    
    def stop(self):
        for module in self.modules.values():
            if isinstance(module, RModule):
                module.quit()

        self.modules['nsm_client'].quit()
        self.modules['jack_tempo'].close()
        super().stop()
    
    def set_tempo(self, bpm: float):
        super().set_tempo(bpm)
        self.modules['jack_tempo'].set_tempo(bpm)
        self.modules['carla'].set_tempo(bpm)
        self.modules['optional_gui'].set_tempo(bpm)
        self.modules['hydrogen'].set_tempo(bpm)
        # self.modules['seq192'].set_tempo(bpm)
    
    def add_main_route(self):
        self.add_route(self._route)
    
    def start_playing(self):
        self.playing = True
        self._route.start_scene(
            'count_beats', self._route.count_beats)
        self._route.start_scene(
            'led_tempo', self._route.led_tempo)
        self.engine.start_cycle()
        
    def stop_playing(self):
        self.playing = False
        self._route.stop_scene('count_beats')
        self._route.stop_scene('led_tempo')
        
    def set_next_signature(self, signature: str):
        self._route.start_scene(
            'next_signature', self._route.change_next_signature,
            signature)
        
    def get_beats_elapsed(self) -> float:
        time_point: int
        
        beats_elapsed = 0.0
            
        for i in range(len(self.tempo_map)):
            time_point, tempo, cycle_len = self.tempo_map[i]
            if i > 0:
                beats_elapsed += (
                    ((time_point - self.tempo_map[i-1][0]) / 60000000000)
                    * self.tempo_map[i-1][1])
                
        beats_elapsed += ((self.current_time - self.tempo_map[-1][0]) / 60000000000
                          * self.tempo_map[-1][1])
        return beats_elapsed

    def set_song(self, song: Union[SongParameters, int]):
        if isinstance(song, int):
            if song < len(SONGS):
                self.song_index = song
                song = SONGS[song]
            else:
                self.logger.critical(f"Song {song} n'existe pas !")
                return
        else:
            self.song_index = SONGS.index(song)
        
        if self.playing:
            self.stop_playing()
        
        self.set_tempo(song.average_tempo)
        self.set_big_sequence(0)
        
        for module in self.modules.values():
            if isinstance(module, RModule):
                module.set_song(song)

    def set_big_sequence(self, big_sequence: int):
        self.big_sequence = big_sequence

        for module in self.modules.values():
            if isinstance(module, RModule):
                module.set_big_sequence(big_sequence)