from typing import TYPE_CHECKING
from mentat import Engine, Route

if TYPE_CHECKING:
    from leonardo import Leonardo


class MainRoute(Route):
    engine: 'MainEngine'
    
    def __init__(self, name: str):
        super().__init__(name)
        
    def led_tempo(self):
        leonardo: 'Leonardo' = self.engine.modules['pedalboard']
        while True:
            j = 0
            while j < self.engine.cycle_length:
                leonardo.send('/note_on', 0, 0x24, 127)
                self.wait(0.01 if j else 0.25, 'beat')
                leonardo.send('/note_off', 0, 0x24)
                
                if j + 1 > self.engine.cycle_length:
                    self.wait_next_cycle()
                else:
                    self.wait(0.99 if j else 0.75, 'beat')
                
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