
from typing import TYPE_CHECKING, Union
from mentat import Module
from enum import IntEnum

from songs import SongParameters

if TYPE_CHECKING:
    from main_engine import MainEngine



class Carla(Module):
    engine: 'MainEngine'
    
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        self.params = dict[SongParameters, dict[str, float]]()
        self._all_paths = set[str]()

    def set_song(self, song: SongParameters):
        print('on y va direc', '/Carla/4/set_parameter_value', 3, 0.8)
        self.send('/Carla_Multi_Client_Carla_7/4/set_parameter_value', 3, 0.8)
        self.send('/register', f"osc.udp://houstonbureau:{self.engine.port}/")
        
    def route(self, address: str, args: list):
        if address in ('//peaks', '//runtime'):
            return

        if address == '//param':
            if args[0] != 5:
                return

        print('lokk', address, args)
        
    def unregister(self):
        self.send('/unregister', f"osc.udp://houstonbureau:{self.engine.port}/")