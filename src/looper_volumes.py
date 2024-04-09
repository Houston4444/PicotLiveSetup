
from rmodule import RModule

class LoooperVolumes(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
    
        self.strips = ('Loop0', 'Loop1', 'Loop2')
        for strip in self.strips:
            self.add_parameter(
                f'{strip}_fader', 
                f'/Non-Mixer-XT.LooperVolumes/strip/{strip}/Gain/Gain%20(dB)/unscaled',
                'f', default=0.0)
        
    def mute_all(self):
        for strip in self.strips:
            self.animate(f'{strip}_fader', None, -70.0, 0.5)
            
    def demute_all(self):
        for strip in self.strips:
            self.animate(f'{strip}_fader', None, 0.0, 0.5)

    def mute(self, strip: str):
        if strip not in self.strips:
            return
        self.animate(f'{strip}_fader', None, -70.0, 0.5)
        
    def demute(self, strip: str):
        if strip not in self.strips:
            return
        self.animate(f'{strip}_fader', None, 0.0, 0.5)