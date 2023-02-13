from typing import TYPE_CHECKING
from mentat import Module

if TYPE_CHECKING:
    from seq192 import Seq192
    from carla_multip import CarlaMultip

class RandomListener(Module):
    def __init__(self, name: str):
        super().__init__(name, protocol='midi')
        
    def route(self, address: str, args: list[int]):
        if address == '/control_change':
            channel, cc, value = args
            if 30 <= cc <= 40 and value > 0:
                seq192: Seq192 = self.engine.modules['seq192']
                seq192.switch_random_sequence(cc_num=cc)
        
        elif address == '/note_on':
            channel, note, velo = args
            
            if channel <= 1 and note <= 43:
                multip: 'CarlaMultip' = self.engine.modules['carla_multip']
                if multip._waiting_demute:
                    print('GO DEMUTE', note)
                multip.demute()
            