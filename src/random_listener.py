from typing import TYPE_CHECKING
from mentat import Module, Engine

if TYPE_CHECKING:
    from seq192 import Seq192

class RandomListener(Module):
    def __init__(self, name: str):
        super().__init__(name, protocol='midi')
        
    def route(self, address: str, args: list[int]):
        if address == '/control_change':
            channel, cc, value = args
            if cc == 30:
                seq192: Seq192 = self.engine.modules['seq192']
                seq192.change_random_sequence()