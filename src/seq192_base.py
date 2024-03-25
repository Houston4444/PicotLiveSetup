
from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Union


from rmodule import RModule
if TYPE_CHECKING:
    from main_engine import MainEngine


@dataclass
class VeloSeq:
    col: int
    row: int
    vel_min: int
    vel_max: int


class Seq192Base(RModule):
    def __init__(self, name: str, port: int):
        super().__init__(name, protocol='osc', port=port)
        self._regular_seqs = [list[int]() for i in range(14)]
        self._map = {}
        self.send('/status/extended')
        
    def route(self, address: str, args: list):
        if address == '/status/extended':
            status_str: str = args[0]
            status_dict: dict = json.loads(status_str)
            
            if status_dict == self._map:
                return
            
            self._map = status_dict.copy()
            
            sequences: list[dict[str, Union[str, int]]] = status_dict.get('sequences')
            if sequences is not None:
                self._read_the_map(sequences)
                
    def _read_the_map(self, sequences: list[dict[str, Union[str, int]]]):
        pass
    
    def clear_selection(self):
        self.send('/panic')
        