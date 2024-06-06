from typing import TYPE_CHECKING
from chansons.song_parameters import SongParameters
from rmodule import RModule

if TYPE_CHECKING:
    from seq192 import Seq192

class RandomListener(RModule):
    def __init__(self, name: str):
        super().__init__(name, protocol='midi')
        
    def route(self, address: str, args: list[int]):
        if address == '/control_change':
            channel, cc, value = args
            if 30 <= cc <= 40 and value > 0:
                seq192: Seq192 = self.engine.modules['seq192']
                seq192.switch_random_sequence(cc_num=cc)
                
    def start(self):
        self.send('/start')
    
    def stop(self):
        self.send('/stop')
        
    def set_song(self, song: SongParameters):
        self.start()

            