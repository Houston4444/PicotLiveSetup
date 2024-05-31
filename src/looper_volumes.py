
from rmodule import RModule


class LoooperVolumes(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
    
        self.strips = ('Loop0', 'Loop1', 'Loop2', 'Loop3')
        for strip in self.strips:
            self.add_parameter(
                f'{strip}_fader', 
                '/Non-Mixer-XT.LooperVolumes/strip/'
                f'{strip}/Gain/Gain%20(dB)/unscaled',
                'f', default=-70.0)
            
            self.add_parameter(
                f'{strip}_mute',
                '/Non-Mixer-XT.LooperVolumes/strip/'
                f'{strip}/Gain/Mute', 'f', default=0.501)
    
    def mute_all(self):
        for strip in self.strips:
            self.animate(f'{strip}_fader', None, -70.0, 0.5)
            self.animate(f'{strip}_mute', None, 0.501, 0.5)
            
    def demute_all(self):
        for strip in self.strips:
            self.set(f'{strip}_mute', 0.0)
            self.animate(f'{strip}_fader', None, 0.0, 0.125)

    def mute(self, strip: str):
        if strip not in self.strips:
            return
        self.animate(f'{strip}_mute', None, 0.501, 0.5)
        self.animate(f'{strip}_fader', None, -70.0, 0.5)
        
    def demute(self, strip: str, volume=0.0):
        if strip not in self.strips:
            return
        self.set(f'{strip}_mute', 0.0)
        self.animate(f'{strip}_fader', None, volume, 0.125)