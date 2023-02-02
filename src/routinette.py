from typing import TYPE_CHECKING
from mentat import Route

if TYPE_CHECKING:
    from leonardo import Leonardo

class Routinette(Route):
    def __init__(self, name: str):
        super().__init__(name)
        
    def blabla(self):
        leonardo: Leonardo = self.engine.modules['pedalboard']
        
        print('pokpozke')
        for i in range(100):
            for j in range(4):
                leonardo.send('/note_on', 0, 0x24, 127)
                self.wait(0.01 if j else 0.25, 'beat')
                leonardo.send('/note_off', 0, 0x24)
                if j == 3:
                    self.wait_next_cycle()
                else:
                    self.wait(0.99 if j else 0.75, 'beat')
            
            
            # self.wait_next_cycle()
            print('ouoummm', i)
            
    
    
    