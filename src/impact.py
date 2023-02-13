import json
from typing import Union

from seq192_base import Seq192Base, VeloSeq
from songs import SongParameters


class Impact(Seq192Base):
    def __init__(self):
        super().__init__('impact', 1444)
        
        self._col = 0
        self._velo_seqs = list[VeloSeq]()

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
        self._velo_seqs.clear()            
        
        for i in range(14):
            self._regular_seqs[i].clear()
        
        for seq in sequences:
            if ' VEL' in seq['name'] and seq['name'].rpartition(' VEL')[2].isdigit():
                velo_max = int(seq['name'].rpartition(' VEL')[2])
                if seq['col'] == last_vel_col:
                    velo_min = last_vel_max + 1
                    if velo_min > velo_max:
                        velo_min = 0
                else:
                    velo_min = 0

                last_vel_max = velo_max
                last_vel_col = seq['col']
                self._velo_seqs.append(
                    VeloSeq(seq['col'], seq['row'], velo_min, velo_max))
            else:
                self._regular_seqs[seq['col']].append(seq['row'])

    def _scene_note_on(self):
        self.send('/play')
        self.wait(0.0625, 'b')
        self.send('/sequence/queue', 'off', 0)
    
    def _scene_note_off(self):
        self.send('/stop')

    def kick_pressed(self, note_on: bool, note: int, velo: int):
        if note_on:
            self.send('/sequence', 'on', self._col, *self._regular_seqs[self._col])
            for velo_seq in self._velo_seqs:
                if velo_seq.col == self._col and velo_seq.vel_min <= velo <= velo_seq.vel_max:
                    self.send('/sequence', 'on', velo_seq.col, velo_seq.row)
            self.start_scene('scene_note', self._scene_note_on)
        else:
            self.clear_selection()
            self.start_scene('scene_note', self._scene_note_off)
            
    def set_song(self, song: SongParameters):
        self._col = song.impact_col