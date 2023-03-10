from typing import TYPE_CHECKING, TypedDict, Union

from mentat import Engine, Route
from non_multip import NonXtMultip
from seq192 import Seq192
from impact import Impact
from leonardo import Leonardo
from ardour import Ardour
from songs import SongParameters, SONGS


class ModulesDict(TypedDict):
    seq192: Seq192
    impact: Impact
    pedalboard: Leonardo
    non_xt_multip: NonXtMultip
    ardour: Ardour


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
        print('set the signiatture', signature)
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
                song = SONGS[song]
            else:
                self.logger.critical(f"Song {song} n'existe pas !")
                return
        
        self.modules['seq192'].set_song(song)
        self.modules['impact'].set_song(song)
        self.modules['non_xt_multip'].set_song(song)
        self.modules['ardour'].set_song(song)