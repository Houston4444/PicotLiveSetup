from rmodule import RModule
from songs import SONGS, SongParameters
from osci_effects import VoxIndex, AmpParam

PFX = '/oscitronix/'

class OsciTronix(RModule):
    def __init__(self, name: str, protocol: str | None = None,
                 port: int | str | None = None, parent= None):
        super().__init__(name, protocol, port, parent)
        
    def route(self, address: str, args: list):
        print('zpofffffoscitronix', address, args)
        
    def set_song(self, song: SongParameters):
        print('mmmfmfoscirtro', song)
        if song.vox_program:
            self.send(PFX + 'load_local_program', song.vox_program)
        # if song is 
        # self.send('/oscitronix/register')
        # self.send('/oscitronix/current/set_param_value',
        #           VoxIndex.AMP.value, AmpParam.MIDDLE.value, 72)
        # self.send('/oscitronix/current/pedal2/speed', 1649)
        # self.send('/oscitronix/current/amp/bass', 92)
        # self.send('/oscitronix/current/program_name', 'Bostonado')
        
    def set_program(self, program_name: str):
        self.send(PFX + 'load_local_program', program_name)