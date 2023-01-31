from mentat import Module

class SooperLooper(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._loop = 0
    
    def set_loop(self, loop: int):
        self._loop = loop

    def hit(self, action: str):
        self.send(f'/sl/{self._loop}/hit', action)