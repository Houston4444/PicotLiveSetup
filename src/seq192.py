from dataclasses import dataclass
import time
import random
from typing import TYPE_CHECKING, Any, Union
import json

from mentat import Module
from threading import Timer

if TYPE_CHECKING:
    from main_engine import MainEngine


@dataclass
class BaseBeatSeq:
    first_col: int
    last_col: int
    signature: str


class SongParameters:
    stop_time = 2.500 # en secondes
    average_tempo = 90.0
    taps_for_tempo = 5
    kick_restarts_cycle = False
    restart_precision: 1.0 # en beats
    restart_acceptability = 0.4 # from 0.0 to 1.0
    tempo_animation_unit = 0.5 # en beats
    tempo_animation_len = 6
    tempo_factor = 0.5
    moving_tempo = 0.00 # en pourcents
    immediate_sequence_switch = False
    tempo_style = 'normal'
    
    # 'average_tempo': 90.00,
    #         'taps_for_tempo': 5,
    #         'kick_restarts_cycle': False,
    #         'restart_precision': 1.0, # en beats
    #         'restart_acceptability': 0.4, # from 0.0 to 1.0
    #         'tempo_animation_unit': 0.5, # en beat
    #         'tempo_animation_len': 6,
    #         'tempo_factor': 0.5,
    #         'moving_tempo': 0.00, # en pourcents
    #         'immediate_sequence_switch': False,
    #         'tempo_style': 'beat'


class Seq192(Module):
    engine: 'MainEngine'
    
    def __init__(self):
        super().__init__('seq192', protocol='osc', port=2354)
        self._last_kick_hit = 0
        self._last_random_change_time = 0
        self._playing = False
        # self._params = {
        #     'stop_time': 2.500, # en secondes
        #     'average_tempo': 90.00,
        #     'taps_for_tempo': 5,
        #     'kick_restarts_cycle': False,
        #     'restart_precision': 1.0, # en beats
        #     'restart_acceptability': 0.4, # from 0.0 to 1.0
        #     'tempo_animation_unit': 0.5, # en beat
        #     'tempo_animation_len': 6,
        #     'tempo_factor': 0.5,
        #     'moving_tempo': 0.00, # en pourcents
        #     'immediate_sequence_switch': False,
        #     'tempo_style': 'beat'
        # }
        self._song = SongParameters()

        self._kick35_note_on = False
        self._kick36_note_on = False

        self._n_taps_done = 0
        self._current_tempo = 120.0
        self._big_sequence = 0
        self._velo_row = 2
        self._random_row = 2

        self._stop_timer = Timer(self._song.stop_time,
                                 self._check_for_stop)

        self._sync_sequence: tuple[int, int] = (0, 0)
        self._base_beat_seqs = list[BaseBeatSeq]()
        
        self._beats_elapsed = 0.0
        self._tempo_change_step = 0.0
        
        self.send('/status/extended')

    def route(self, address: str, args: list):
        if address == '/status/extended':
            status_str: str = args[0]
            status_dict: dict = json.loads(status_str)
            
            sequences: list[dict[str, Union[str, int]]] = status_dict.get('sequences')
            if sequences is not None:
                self._read_the_map(sequences)
    
    def _read_the_map(self, sequences:list[dict[str, Union[str, int]]]):
        self._base_beat_seqs.clear()
        
        if sequences:
            last_col = sequences[-1]['col']
        else:
            last_col = 0

        for seq in sequences:
            if seq['row'] == 0 and seq['name'].endswith(' BB'):
                if self._base_beat_seqs:
                    self._base_beat_seqs[-1].last_col = seq['col'] - 1
                self._base_beat_seqs.append(
                    BaseBeatSeq(seq['col'], 0, seq['time']))
                
        if self._base_beat_seqs:
            self._base_beat_seqs[-1].last_col = last_col

        print(self._base_beat_seqs)
        
    def _get_cols_for_base_seqs(self, base_seq: int) -> list[int]:        
        if len(self._base_beat_seqs) > base_seq:
            return list(range(self._base_beat_seqs[base_seq].first_col,
                              self._base_beat_seqs[base_seq].last_col + 1))
        
        return []
    
    def _animate_tempo(self):
        for i in range(self._song.tempo_animation_len):
            self.wait(self._song.tempo_animation_unit, 'beat')
            self.set_tempo(self._current_tempo + self._tempo_change_step)
    
    def start(self):
        self._beats_elapsed = 0.0
        self.send('/cursor', 0.0)
        self.send('/play')
        self.engine.set_tempo(self._current_tempo)
        self.engine.set_time_signature('4/4')
        self.engine.start_playing()
        self._playing = True
        
    def stop(self):
        self.send('/stop')
        self._playing = False
        self.engine.stop_playing()
        self._velo_row = 2
        
    def set_tempo(self, tempo: float):
        self._current_tempo = tempo
        self.send('/bpm', tempo)
        self.engine.set_tempo(tempo)
    
    def clear_selection(self):
        self.send('/panic')
    
    def set_velo_row(self, velo: int):
        velo_row: int
        
        if velo <= 32:
            velo_row = 2
        elif velo <= 64:
            velo_row = 3
        elif velo <= 96:
            velo_row = 4
        else:
            velo_row = 5
            
        if velo_row !=  self._velo_row:
            self.send('/sequence', 'off', self._big_sequence * 2, self._velo_row)
            self.send('/sequence', 'on', self._big_sequence * 2, velo_row)
            self._velo_row = velo_row
    
    def set_big_sequence(self, big_sequence: int):
        ex_cols = self._get_cols_for_base_seqs(self._big_sequence)
        new_cols = self._get_cols_for_base_seqs(big_sequence)
        
        if not (ex_cols and new_cols):
            return
        
        if self._song.immediate_sequence_switch:
            for ex_col in ex_cols:
                self.send('/sequence', 'off', ex_col)
            
            for new_col in new_cols:
                self.send('/sequence', 'on', new_col, 0, 1)

            self.send('/sequence', 'on', big_sequence * 2, self._velo_row)
            self.send('/sequence', 'on', 1 + big_sequence * 2, self._random_row)
        else:
            self._sync_sequence = (ex_cols[0], 0)
            self.send('/sequence', 'sync', *self._sync_sequence)
            
            for ex_col in ex_cols:
                self.send('/sequence/queue', 'off', ex_col)
                
            for new_col in new_cols:
                self.send('/sequence/queue', 'on', new_col, 0, 1)

            self.send('/sequence/queue', 'on', big_sequence * 2, self._velo_row)
            self.send('/sequence/queue', 'on', 1 + big_sequence * 2, self._random_row)
            
            if (len(self._base_beat_seqs) > big_sequence
                    and self._base_beat_seqs[self._big_sequence].signature
                        != self._base_beat_seqs[big_sequence].signature):
                self.engine.set_next_signature(
                    self._base_beat_seqs[big_sequence].signature)
                
        self._big_sequence = big_sequence
        
    def _check_for_stop(self):
        if self._kick36_note_on:
            self.stop()
    
    def _get_bpm_from_average(self, bpm: float) -> tuple[bool, float]:
        valid_bpm = True
        aver_bpm = self._song.average_tempo
        tempo_style = self._song.tempo_style
        
        if tempo_style == 'valse':
            if bpm < aver_bpm / 3.5:
                valid_bpm = False
            elif bpm < aver_bpm / 2.5:
                bpm *= 3
            elif bpm < aver_bpm / 1.25:
                valid_bpm = False
            elif bpm < aver_bpm / 0.75:
                pass
            else:
                valid_bpm = False
        elif tempo_style == 'binaire':
            if bpm < aver_bpm / 5:
                valid_bpm = False
            elif bpm < aver_bpm / 3:
                bpm *= 4
            elif bpm < aver_bpm / 1.5:
                bpm *= 2
            elif bpm < aver_bpm / 0.75:
                pass
            elif bpm < aver_bpm / 0.33:
                bpm *= 0.5
            else:
                valid_bpm = False
        elif tempo_style == 'beat':
            if bpm < aver_bpm / 5:
                valid_bpm = False
            
        else:
            if bpm < aver_bpm / 5:
                valid_bpm = False
            elif bpm < aver_bpm / 3.5:
                bpm *= 4
            elif bpm < aver_bpm / 2.5:
                bpm *= 3
            elif bpm < aver_bpm / 1.75:
                bpm *= 2
            elif bpm < aver_bpm / 1.25:
                bpm *= 1.5
            elif bpm < aver_bpm / 0.75:
                pass
            elif bpm < aver_bpm / 0.4:
                bpm *= 0.5
            else:
                valid_bpm = False
        
        return valid_bpm, bpm
    
    def kick_pressed(self, note_on: int, note: int, velo: int):
        self._kick36_note_on = note_on        
        if not note_on:
            self._stop_timer.cancel()
            return
        
        kick_time = time.time()

        # gérer le timer pour stopper seq192 si la note off n'apparaît
        # pas dans le délai imparti
        self._stop_timer.cancel()
        del self._stop_timer
        self._stop_timer = Timer(self._song.stop_time,
                                    self._check_for_stop)
        self._stop_timer.start()

        if self._playing:
            mv_tempo = self._song.moving_tempo / 100
            restart_cycle = self._song.kick_restarts_cycle
            
            if mv_tempo > 0.0 and not restart_cycle:
                bpm = 60 / (kick_time - self._last_kick_hit)
                valid_bpm, bpm = self._get_bpm_from_average(bpm)
                if valid_bpm:
                    new_tempo = mv_tempo * bpm + (1 - mv_tempo) * self._current_tempo
                    self.set_tempo(new_tempo)
            
            if restart_cycle:
                beats_elapsed = self._beats_elapsed + self.engine.get_beats_elapsed()
                beat_precision = self._song.restart_precision
                restart_acceptability = self._song.restart_acceptability
                tempo_factor: float = self._song.tempo_factor
                n_beat_prec, floating = divmod(beats_elapsed, beat_precision)
                beat_before = n_beat_prec * beat_precision
                floating_ratio = floating / beat_precision

                place: float
                new_tempo = self._current_tempo
                
                if floating_ratio < (restart_acceptability * 0.5):
                    place = beat_before
                    new_tempo =  self._current_tempo / (1.0 + floating_ratio * tempo_factor)
                elif floating_ratio > (1 - (restart_acceptability * 0.5)):
                    place = beat_before + beat_precision
                    new_tempo = self._current_tempo / (1 - ((1 -floating_ratio) * tempo_factor)) 

                if new_tempo != self._current_tempo:
                    # self.set_tempo(new_tempo)
                    self._tempo_change_step = ((new_tempo - self._current_tempo)
                                               / self._song.tempo_animation_len)
                    print('beats elpapsed', beats_elapsed, place)
                    print('neuue tempo', self._current_tempo, new_tempo, self._tempo_change_step)
                    self.start_scene('animate_tempo', self._animate_tempo)
                    
                    self.send('/cursor', place)
                    self._beats_elapsed = place
                    self.engine.start_cycle()
                    print('SPZ', place, self.engine.tempo)
        else:
            aver_bpm: self._song.average_tempo
            taps_for_tempo = self._song.taps_for_tempo
            start_play = False

            if taps_for_tempo == 1:
                self.set_tempo(aver_bpm)
                start_play = True
            else:
                bpm = 60 / (kick_time - self._last_kick_hit)
                valid_bpm, bpm = self._get_bpm_from_average(bpm)
                if valid_bpm:
                    self._n_taps_done += 1
                else:
                    self._n_taps_done = 1

                if valid_bpm and self._n_taps_done >= taps_for_tempo:
                    self.set_tempo(bpm)
                    start_play = True

            if start_play:
                self._random_row = 2
                self.clear_selection()
                self.send('/sequence', 'on', self._big_sequence * 2, 0, 1)
                self.send('/sequence', 'on', 1 + self._big_sequence * 2, 0, 1)
                self.send('/sequence', 'on',
                          1 + self._big_sequence * 2, self._random_row)
                self.start()
        
        self.set_velo_row(velo)
        self._last_kick_hit = kick_time
        
    def change_random_sequence(self):
        if time.time() - self._last_random_change_time < 0.5:
            return
        
        random_row = self._random_row
        while random_row == self._random_row:
            random_row = random.randint(2, 6)
        
        self.send('/sequence', 'off',
                  1 + self._big_sequence * 2, self._random_row)
        self.send('/sequence', 'on', 1 + self._big_sequence * 2, random_row)
        self._random_row = random_row
        self._last_random_change_time = time.time()