from mentat import Module

class Seq192(Module):
    def __init__(self):
        super().__init__('seq192', protocol='osc', port=2354)
        
    def start(self):
        self.send('/play')
        
    def stop(self):
        self.send('/stop')
        
    def set_tempo(self, tempo: float):
        self.send('/bpm', tempo)