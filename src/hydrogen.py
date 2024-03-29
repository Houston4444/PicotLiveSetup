from rmodule import RModule

class Hydrogen(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
    def set_tempo(self, bpm: float):        
        self.send('/Hydrogen/BPM', bpm)
