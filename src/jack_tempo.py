import jacklib
from jacklib import JackOptions, jack_position_t
from mentat import Module
from ctypes import cdll, CDLL, POINTER, c_double, RTLD_LOCAL
import sys
from pathlib import Path

class JackTempoSetter(Module):
    def __init__(self, name: str):
        super().__init__(name)
        
        self.current_tempo = 120.0
        self.jack_client = jacklib.client_open(
            'tempo_setter',
            JackOptions.NO_START_SERVER | JackOptions.SESSION_ID,
            None)
        jacklib.activate(self.jack_client)
        
        this_path = Path(__file__)
        self.so_file = cdll.LoadLibrary('libjack.so.0')
        self.so_file = cdll.LoadLibrary(str(this_path.parent / 'timebase_master.so'))
        
        # self._set_master()
        jacklib.set_timebase_callback(
            self.jack_client, 0, self.so_file.TimebaseCallback, 0)

        pos = jacklib.jack_position_t()
        pos.valid = 0x10
        pos.beats_per_minute = 121.0
        jacklib.transport_reposition(self.jack_client, pos)        

    def close(self):
        jacklib.client_close(self.jack_client)
    
    def set_tempo(self, tempo: float):
        self.so_file.set_tempo(c_double(tempo))
        
        jacklib.set_timebase_callback(
            self.jack_client, 0, self.so_file.TimebaseCallback, 0)

        pos = jacklib.jack_position_t()
        pos.valid = 0x10
        pos.beats_per_minute = tempo
        print('jack set tempo', tempo)
        jacklib.transport_reposition(self.jack_client, pos)