from typing import TYPE_CHECKING

from nsm import NsmClient
if TYPE_CHECKING:
    from seq192 import Seq192
    

class NsmMentator(NsmClient):
    def __init__(self):
        super().__init__('ElMentator', 'el_mentator')
        
    def save(self) -> tuple[int, str]:
        seq192: Seq192 = self.engine.modules['seq192']
        seq192.send('/status/extended')
        return (0, 'Saved')
        
        