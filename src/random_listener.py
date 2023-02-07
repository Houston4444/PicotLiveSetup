from typing import TYPE_CHECKING
from mentat import Module

if TYPE_CHECKING:
    from seq192 import Seq192

class RandomListener(Module):
    def __init__(self, name: str):
        super().__init__(name, protocol='midi')
        
    def route(self, address: str, args: list[int]):
        if address == '/control_change':
            channel, cc, value = args
            if 30 <= cc <= 40:
                if cc == 31: print('zonie', cc)
                seq192: Seq192 = self.engine.modules['seq192']
                seq192.switch_random_sequence(cc_num=cc)