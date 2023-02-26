from mentat import Module
from songs import SongParameters


class Ardour(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
    def set_song(self, song: SongParameters):
        self.send('/recall_mixer_scene', song.ardour_scene)