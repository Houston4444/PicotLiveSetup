import time
import random
from typing import TYPE_CHECKING, Any, Union
import json

from mentat import Module
from threading import Timer

from mentat.engine import Engine
if TYPE_CHECKING:
    from routinette import Routinette

class Seq192(Module):
    def __init__(self, routinette: 'Routinette'):
        super().__init__('seq192', protocol='osc', port=2354)
        self._routinette = routinette
        self._last_kick_hit = 0
        self._last_random_change_time = 0
        self._playing = False
        self._params = {
            'stop_time': 2.500, # en secondes
            'average_tempo': 99.00,
            'taps_for_tempo': 1,
            'kick_restarts_cycle': False,
            'moving_tempo': 50.00, # in percents
            'immediate_sequence_switch': False
        }
        
        self._kick35_note_on = False
        self._kick36_note_on = False
        
        self._n_taps_done = 0
        self._current_tempo = 120.0
        self._big_sequence = 0
        self._velo_row = 2
        self._random_row = 2
        
        self._stop_timer = Timer(self._params['stop_time'],
                                 self._check_for_stop)
        
        self._sync_sequence: tuple[int, int] = (0, 0)

    def route(self, address: str, args: list):
        if address == '/status/extended':
            status_str: str = args[0]
            status_dict: dict = json.loads(status_str)
            
            sequences: list[dict[str, Union[str, int]]] = status_dict.get('sequences')
            if sequences is None:
                return
            for seq in sequences:
                if (seq['col'], seq['row']) == self._sync_sequence:
                    print(time.time())
                    print('Sync sequence is playing', seq['playing'])
                    break
    
    def start(self):        
        self.send('/play')
        self.engine.set_tempo(self._current_tempo)
        self.engine.set_time_signature('4/4')
        self._routinette.activate()
        self._routinette.start_scene('pilpili', self._routinette.blabla)
        self.engine.start_cycle()
        self._playing = True
        
    def stop(self):
        self._routinette.stop_scene('pilpili')
        self.send('/stop')
        self._playing = False
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
        immediate: bool = self._params['immediate_sequence_switch']
        if immediate:
            self.send('/sequence', 'off', self._big_sequence * 2)
            self.send('/sequence', 'off', 1 + self._big_sequence * 2)
            self.send('/sequence', 'on', big_sequence * 2, 0, 1)
            self.send('/sequence', 'on', 1 + big_sequence * 2, 0, 1)
            self.send('/sequence', 'on', big_sequence * 2, self._velo_row)
            self.send('/sequence', 'on', 1 + big_sequence * 2, self._random_row)
        else:
            self._sync_sequence = (self._big_sequence * 2, 0)
            print(time.time())
            self.send('/status/extended')
            self.send('/sequence', 'sync', self._big_sequence * 2, 0)            
            self.send('/sequence/queue', 'off', self._big_sequence * 2)
            self.send('/sequence/queue', 'off', 1 + self._big_sequence * 2)
            self.send('/sequence/queue', 'on', big_sequence * 2, 0, 1)
            self.send('/sequence/queue', 'on', 1 + big_sequence * 2, 0, 1)
            self.send('/sequence/queue', 'on', big_sequence * 2, self._velo_row)
            self.send('/sequence/queue', 'on', 1 + big_sequence * 2, self._random_row)
        self._big_sequence = big_sequence
        
    def _check_for_stop(self):
        if self._kick36_note_on:
            self.stop()
    
    def _get_bpm_from_average(self, bpm: float) -> tuple[bool, float]:
        valid_bpm = True
        aver_bpm: float = self._params['average_tempo']
                    
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
        self._stop_timer = Timer(self._params['stop_time'],
                                    self._check_for_stop)
        self._stop_timer.start()

        if self._playing:
            mv_tempo: float = self._params['moving_tempo'] / 100
            restart_cycle: bool = self._params['kick_restarts_cycle']
            
            if mv_tempo > 0.0:
                bpm = 60 / (kick_time - self._last_kick_hit)
                valid_bpm, bpm = self._get_bpm_from_average(bpm)
                if valid_bpm:
                    self.set_tempo(
                        mv_tempo * bpm + (1 - mv_tempo) * self._current_tempo)
            
            if restart_cycle:
                self.start()

        else:
            aver_bpm: float = self._params['average_tempo']
            taps_for_tempo: int = self._params['taps_for_tempo']
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
                print('oenzier', self._n_taps_done)
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