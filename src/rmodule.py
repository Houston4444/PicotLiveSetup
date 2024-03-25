from typing import TYPE_CHECKING
from mentat import Module

from songs import SongParameters

if TYPE_CHECKING:
    from main_engine import MainEngine

class RModule(Module):
    engine: 'MainEngine'
    
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
    def set_song(self, song: SongParameters):
        ...
        
    def set_big_sequence(self, big_sequence: int):
        ...