from typing import TYPE_CHECKING
from rmodule import RModule
from songs import SONGS

if TYPE_CHECKING:
    from chansons.song_parameters import SongParameters


class Trigger(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
    
    def route(self, address: str, args: list):
        if address == '/note_on':
            song: SongParameters = SONGS[self.engine.song_index]
            song.trigger_event()