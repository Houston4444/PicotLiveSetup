from dataclasses import dataclass
import time
import random
from typing import TYPE_CHECKING, Optional, Union
import json
from threading import Timer

from mentat import Module
from songs import Orage, SongParameters
from seq192_base import VeloSeq, Seq192Base
from songs import SONGS
from sooperlooper import SooperLooper

if TYPE_CHECKING:
    from main_engine import MainEngine
    from non_multip import NonXtMultip





@dataclass
class RandomGroup:
    col: int
    rows: list[int]
    cc: int
    
    def __post_init__(self):
        self.playing_row_index = -1
        self.last_switch_time = 0.0


@dataclass
class CondSeq:
    col: int
    row: int
    starts: bool
    regular: bool
    ends: bool


@dataclass
class BaseBeatSeq:
    first_col: int
    last_col: int
    signature: str
    
    def get_n_beats(self) -> float:
        return float(self.signature.split('/')[0])


class Seq192(Seq192Base):
    def __init__(self):
        super().__init__('seq192', 2354)
        # super().__init__('seq192', protocol='osc', port=2354)
        self._last_kick_hit = 0
        self._playing = False
        self._song = SongParameters()

        self._kick35_note_on = False
        self._kick36_note_on = False

        self._n_taps_done = 0
        self._last_kick_velo = 100
        self._current_tempo = 120.0
        self._big_sequence = 0
        self._next_big_sequence = 0
        self._switching_big_sequence = False

        self._sync_sequence = (0, 0)
        self._base_beat_seqs = list[BaseBeatSeq]()
        self._velo_seqs = list[VeloSeq]()
        self._random_groups = list[RandomGroup]()
        self._cond_seqs = list[CondSeq]()
        
        self._beats_elapsed = 0.0
        self._tempo_change_step = 0.0
        
    def set_song(self, song: SongParameters):
        self._song = song
        self.send('/screenset', song.seq_page)
        self.send('/status/extended')

    def _read_the_map(self, sequences:list[dict[str, Union[str, int]]]):
        self._base_beat_seqs.clear()
        self._velo_seqs.clear()
        self._random_groups.clear()
        self._cond_seqs.clear()

        for i in range(14):
            self._regular_seqs[i].clear()

        last_vel_max = 0
        last_vel_col = -1

        for seq in sequences:
            if seq['row'] == 0 and seq['name'].endswith(' BB'):
                if self._base_beat_seqs:
                    self._base_beat_seqs[-1].last_col = seq['col'] - 1
                self._base_beat_seqs.append(
                    BaseBeatSeq(seq['col'], 0, seq['time']))
                self._regular_seqs[seq['col']].append(seq['row'])
            
            elif ' VEL' in seq['name'] and seq['name'].rpartition(' VEL')[2].isdigit():
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

            elif ' RD' in seq['name'] and seq['name'].rpartition(' RD')[2].isdigit():
                cc_num = 30 + int(seq['name'].rpartition(' RD')[2])
                if (self._random_groups
                        and self._random_groups[-1].col == seq['col']
                        and self._random_groups[-1].rows[-1] == seq['row'] - 1
                        and cc_num == self._random_groups[-1].cc):
                    self._random_groups[-1].rows.append(seq['row'])
                else:
                    self._random_groups.append(
                        RandomGroup(seq['col'], [seq['row']], cc_num))
        
            elif seq['name'].endswith(
                    (' ___', ' X__', ' XX_', ' X_X', ' _X_', ' _XX', ' __X')):
                cond_str = seq['name'][-3:]
                starts_x, regular_x, ends_x = cond_str
                self._cond_seqs.append(
                    CondSeq(seq['col'],
                            seq['row'],
                            starts_x == 'X',
                            regular_x == 'X',
                            ends_x == 'X'))
            else:
                self._regular_seqs[seq['col']].append(seq['row'])
                            
        if sequences:
            last_col = sequences[-1]['col']
        else:
            last_col = 0
            
        if self._base_beat_seqs:
            self._base_beat_seqs[-1].last_col = last_col

        timer = Timer(1.0, self.send, ['/status/extended'])
        timer.start()
        
    def _get_cols_for_base_seqs(self, base_seq: int) -> list[int]:        
        if len(self._base_beat_seqs) > base_seq:
            return list(range(self._base_beat_seqs[base_seq].first_col,
                              self._base_beat_seqs[base_seq].last_col + 1))
        
        return []

    def _animate_tempo(self):
        '''scene method'''
        for i in range(self._song.tempo_animation_len):
            self.wait(self._song.tempo_animation_unit, 'beat')
            self.set_tempo(self._current_tempo + self._tempo_change_step)

    def _change_big_sequence_later(self):
        '''scene method'''
        self._switching_big_sequence = True
        self.wait_next_cycle()
        if (len(self._base_beat_seqs) > self._next_big_sequence
                and self._base_beat_seqs[self._big_sequence].signature
                    != self._base_beat_seqs[self._next_big_sequence].signature):
            self.engine.set_next_signature(
                self._base_beat_seqs[self._next_big_sequence].signature)

        self._big_sequence = self._next_big_sequence
        self._switching_big_sequence = False        
        cols = self._get_cols_for_base_seqs(self._big_sequence)
        
        self._sync_sequence = (self._base_beat_seqs[self._big_sequence].first_col, 0)
        self.send('/sequence', 'sync', *self._sync_sequence)
        
        # normally, /sequence/queue made the origin sequence 'off'
        # but in case user press on many sequences changes
        # we need to set off all the non playing sequences
        for i in range(14):
            if i not in cols:
                self.send('/sequence', 'off', i)
                
        self.wait(0.125, 'beat')
        
        for cond_seq in self._cond_seqs:
            if cond_seq.col in cols:
                if cond_seq.starts and not cond_seq.regular:
                    self.send('/sequence/queue', 'off',
                              cond_seq.col, cond_seq.row)
                elif not cond_seq.starts and cond_seq.regular:
                    self.send('/sequence/queue', 'on',
                              cond_seq.col, cond_seq.row)

    def _check_for_stop(self):
        '''scene method'''
        open_secs = (self._song.open_time_beats
                     * 60.0 / self.engine.tempo) 

        self.wait(open_secs, 's')
        if self._kick36_note_on:
            print('c la ksas pass')
            self.engine.modules['sooperlooper'].mute_all(kick=True)

        self.wait(self._song.stop_time - open_secs, 's')
        
        if self._kick36_note_on:
            self.stop()
            self.engine.modules['randomidi'].stop()
            self.engine.modules['sooperlooper'].stop_play_song()

    def start(self):
        self._beats_elapsed = 0.0
        self.send('/cursor', 0.0)
        # self.send('/swing/reference', 8)
        # self.send('/swing', 1)
        self.send('/play')
        self.engine.set_tempo(self._current_tempo)
        if self._base_beat_seqs:
            self.engine.set_time_signature(self._base_beat_seqs[0].signature)
        else:
            self.engine.set_time_signature('4/4')
        self.engine.start_playing()
        self._playing = True
        
    def stop(self):
        self.send('/stop')
        self._playing = False
        self.engine.stop_playing()
        
    def set_tempo(self, tempo: float):
        self._current_tempo = tempo
        self.send('/bpm', tempo)
        self.engine.set_tempo(tempo)
    
    def switch_velo_seqs(self, velo: int, big_sequence: int):
        cols = self._get_cols_for_base_seqs(big_sequence)
        for velo_seq in self._velo_seqs:
            if velo_seq.col not in cols:
                continue
            
            word = 'on' if velo_seq.vel_min <= velo <= velo_seq.vel_max else 'off'
            self.send('/sequence', word, velo_seq.col, velo_seq.row)
    
    def set_big_sequence(self, big_sequence: int):
        if big_sequence == self._big_sequence:
            return
        
        ex_cols = self._get_cols_for_base_seqs(self._big_sequence)
        new_cols = self._get_cols_for_base_seqs(big_sequence)

        if not (ex_cols and new_cols):
            return

        immediate = self._song.immediate_sequence_switch or not self._playing

        if not immediate:
            beats_elapsed = self.engine.get_beats_elapsed()
            if (beats_elapsed 
                        % self._base_beat_seqs[self._big_sequence].get_n_beats() < 1.0
                    and beats_elapsed
                        % self._base_beat_seqs[big_sequence].get_n_beats() < 1.0):
                immediate = True 

        if immediate:
            for ex_col in ex_cols:
                self.send('/sequence', 'off', ex_col)
            
            for new_col in new_cols:
                for row in self._regular_seqs[new_col]:
                    self.send('/sequence', 'on', new_col, row)
                for cond_seq in self._cond_seqs:
                    if cond_seq.col == new_col and cond_seq.starts:
                        self.send('/sequence', 'on', new_col, cond_seq.row)

            self.switch_velo_seqs(self._last_kick_velo, big_sequence)
            self.switch_random_sequence(big_sequence)
            self._big_sequence = big_sequence
        else:
            self._sync_sequence = (ex_cols[0], 0)
            self._next_big_sequence = big_sequence
            self.send('/sequence', 'sync', *self._sync_sequence)

            for cond_seq in self._cond_seqs:
                if cond_seq.col in ex_cols:
                    if cond_seq.ends:
                        self.send('/sequence', 'on', cond_seq.col, cond_seq.row)
                    else:
                        self.send('/sequence', 'off', cond_seq.col, cond_seq.row)
                elif cond_seq.col in new_cols:
                    if cond_seq.starts:
                        self.send('/sequence/queue', 'on', cond_seq.col, cond_seq.row)
                    else:
                        self.send('/sequence/queue', 'off', cond_seq.col, cond_seq.row)

            for ex_col in ex_cols:
                self.send('/sequence/queue', 'off', ex_col)

            for new_col in new_cols:
                if self._regular_seqs[new_col]:
                    self.send('/sequence/queue', 'on', new_col,
                              *self._regular_seqs[new_col])
                    
            for random_gp in self._random_groups:
                if len(random_gp.rows) >= 2 and random_gp.col in new_cols:
                    random_gp.playing_row_index = 0
                    self.send('/sequence/queue', 'on',
                              random_gp.col, random_gp.rows[0])
                    self.send('/sequence/queue', 'off',
                              random_gp.col, *random_gp.rows[1:])

            self.switch_velo_seqs(self._last_kick_velo, big_sequence)
            # self.switch_random_sequence(big_sequence)
            
            self.start_scene('switch_big_sequence',
                             self._change_big_sequence_later)
    
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
        
        self.stop_scene('check_for_stop')
        if not note_on:
            self.engine.modules['sooperlooper'].demute_all(kick=True)
            return
        
        kick_time = time.time()

        # gérer le timer pour stopper seq192 si la note off n'apparaît
        # pas dans le délai imparti
        
        self.start_scene('check_for_stop', self._check_for_stop)
        
        # self._stop_timer.cancel()
        # del self._stop_timer
        # self._stop_timer = Timer(self._song.stop_time,
        #                          self._check_for_stop)
        # self._stop_timer.start()

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
                    self._tempo_change_step = ((new_tempo - self._current_tempo)
                                               / self._song.tempo_animation_len)
                    self.start_scene('animate_tempo', self._animate_tempo)
                    
                    self.send('/cursor', place)
                    self._beats_elapsed = place
                    self.engine.start_cycle()
        else:
            aver_bpm = self._song.average_tempo
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
                self.clear_selection()
                cols = self._get_cols_for_base_seqs(self._big_sequence)
                for col in cols:
                    if self._regular_seqs[col]:
                        self.send('/sequence', 'on', col,
                                  *self._regular_seqs[col])

                for random_gp in self._random_groups:
                    if random_gp.col in cols:
                        random_gp.playing_row_index = 0
                        self.send('/sequence', 'on',
                                  random_gp.col, random_gp.rows[0])
                self.start()
                # self.engine.modules['randomidi'].start()
                self.engine.modules['sooperlooper'].start_play_song()
                    # self.engine.modules['sooperlooper'].orage_rec()
        
        self.switch_velo_seqs(velo, self._big_sequence)
        self._last_kick_hit = kick_time

    def switch_random_sequence(self, big_sequence: Optional[int]=None,
                               cc_num: Optional[int]=None):
        if self._switching_big_sequence:
            return
            
        if big_sequence is None:
            big_sequence = self._big_sequence

        cols = self._get_cols_for_base_seqs(big_sequence)
        
        for random_gp in self._random_groups:
            if (len(random_gp.rows) <= 1
                    or random_gp.col not in cols
                    or time.time() - random_gp.last_switch_time < 0.5
                    or (cc_num is not None and random_gp.cc != cc_num)):
                continue

            random_index = random_gp.playing_row_index
            while random_index == random_gp.playing_row_index:
                random_index = random.randint(0, len(random_gp.rows) - 1)

            self.send('/sequence', 'off', random_gp.col,
                      random_gp.rows[random_gp.playing_row_index])
            self.send('/sequence', 'on', random_gp.col,
                      random_gp.rows[random_index])
            random_gp.playing_row_index = random_index 
            random_gp.last_switch_time = time.time()