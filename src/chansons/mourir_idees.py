from enum import Enum, auto
from json import load
import time
from typing import TYPE_CHECKING

from chansons.orage import N_LOOPS
from chansons.song_parameters import SongParameters, scene_method, Marker, REPETTE
from enums import FsButton


class Marker(Marker):
    DEBUT = auto()
    COUPLET_1 = auto()
    JUGEANT_QUIL = auto()
    SAINTS_JEANS = auto()
    SACRIFICE = auto()
    HECATOMBES = auto()
    BOUTEFEUX = auto()
    

START_MARKER = Marker.DEBUT

ALL = -1
ARPEGE_TZOU = 0
RYTHME_TZOU = 1
AIGUS = 2
BASSE = 3
TZOU_DRUM = 4
N_LOOPS = 5


class TzouDrumState(Enum):
    OFF = 0
    REC = 1
    DONE = 2


class MourirIdees(SongParameters):
    average_tempo = 112
    seq_page = 12
    immediate_sequence_switch = True
    kick_velo_ratio = 0.0
    drum_velocity = 80.0
    
    def __init__(self):
        super().__init__()
        self.scenes = [self.main_scene]
        
        self._tzou_drum_state = TzouDrumState.OFF
    
    def add_marker(self, marker: Marker):
        self._current_marker = marker
        
        if not REPETTE or marker is START_MARKER:
            self._repette_started = True
    
    def loop_sl(self, loop: int, updown: str, action: str):
        if REPETTE and not self._repette_started:
            return
        self.engine.modules['sooperlooper'].sl(loop, updown, action)
    
    def loop_sls(self, loops: list[int], updown: str, action: str):
        if REPETTE and not self._repette_started:
            return
        soop = self.engine.modules['sooperlooper']
        for loop in loops:
            soop.sl(loop, updown, action)
    
    def set_engine(self, engine):
        super().set_engine(engine)
    
    def stop_main_scene(self):
        super().stop_main_scene()
        self.engine.stop_scene('la_chanson')
        soop = self.engine.modules['sooperlooper']
        soop.mute_all()
        soop.sl(-1, 'hit', 'pause')
        self._tzou_drum_state = TzouDrumState.OFF
    
    @scene_method()
    def la_chanson(self):
        self._repette_started = not REPETTE
        
        seq192 = self.engine.modules['seq192']
        oscitronix = self.engine.modules['oscitronix']
        randomidi = self.engine.modules['randomidi']
        carla = self.engine.modules['carla']
        soop = self.engine.modules['sooperlooper']
        multip = self.engine.modules['non_xt_multip']
                
        self.add_marker(Marker.DEBUT)
        
        seq192.set_big_sequence(0)
        
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 0.0)
        carla.set_param_str('InputGain', 'Gain', 1.0)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Wet amount', 0.2176)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Dry enable', 0.0)
        carla.set_param_str('TzouMagnetik', 'Output gain', 1.0)
        carla.set_param_str('TzouMagnetik', 'Wet post-process', 0.0)
        
        multip.set_velocity(70.0)
        
        soop.set_n_loops(N_LOOPS)
        soop.reset_sync_pos_all()
        soop.mute(ARPEGE_TZOU)
        soop.mute(RYTHME_TZOU)
        soop.mute(AIGUS)
        soop.mute(BASSE)
                
        self.engine.wait_next_cycle()
        randomidi.start()
        seq192.start()
        
        self.wait(16)

        self.loop_sls([ARPEGE_TZOU, RYTHME_TZOU, AIGUS, BASSE],
                      'down', 'record')
        soop.demute(ARPEGE_TZOU)
        soop.demute(AIGUS)
        
        self.wait(70) # 70 | 0
        
        self.loop_sls([ARPEGE_TZOU, RYTHME_TZOU, AIGUS, BASSE],
                      'up', 'record')
        
        soop.trigger_all()
        self.wait(8)
        soop.trigger_all()
        
        self.add_marker(Marker.JUGEANT_QUIL)
        
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 1.0)
        self.wait(32)
        self.loop_sl(BASSE, 'down', 'replace')
        soop.demute(BASSE)
        self.wait(38) # 70 | 0

        soop.trigger_all()
        multip.set_velocity(80.0)
        
        seq192.set_big_sequence(1)
        seq192.send('/cursor', 0.0)
        self.wait(8)
        soop.trigger_all()
        self.wait(8)
        soop.trigger_all()
        
        self.add_marker(Marker.SAINTS_JEANS)
        
        self.loop_sl(BASSE, 'down', 'replace')
        self.wait(32)
        self.loop_sl(BASSE, 'up', 'replace')
        self.wait(8)
        
        randomidi.stop()
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 0.0)
        carla.set_param_str('InputGain', 'Gain', 0.5)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Delay 0 on', 0.0)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Delay 2 on', 0.0)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Wet amount', 0.080)
        
        multip.animate_velocity(80.0, 100.0, 30.0)
        self.wait(30)
        
        soop.trigger_all()

        seq192.send('/cursor', 0.0)
        seq192.set_big_sequence(2)
        multip.set_velocity(100.0)
        soop.mute(TZOU_DRUM)
        
        self.wait(8)
        soop.trigger_all()
        self.wait(8)
        soop.trigger_all()
        
        self.add_marker(Marker.SACRIFICE)
        
        self.loop_sl(RYTHME_TZOU, 'down', 'replace')
        soop.demute(RYTHME_TZOU)
        self.wait(70)
        self.loop_sl(RYTHME_TZOU, 'up', 'replace')
        
        seq192.send('/cursor', 0.0)
        
        soop.trigger_all()
        self.wait(4)
        soop.trigger_all()
        
        self.add_marker(Marker.HECATOMBES)
        
        self.wait(32)
        soop.sl(ALL, 'hit', 'set_sync_pos')
        self.wait(38)
        carla.set_param_str('InputGain', 'Gain', 0.60)
        carla.set_param_str('ChannelB Tzous', 'ChannelB', 1.0)
        soop.trigger_all()
        seq192.send('/cursor', 0.0)
        soop.sl(ALL, 'hit', 'reset_sync_pos')
        self.wait(38)
        seq192.send('/cursor', 0.0)
        soop.trigger_all()
        
        self.wait(8)
        soop.trigger_all()
        self.wait(8)
        soop.trigger_all()

        carla.set_param_str('InputGain', 'Gain', 0.3)
        self.add_marker(Marker.BOUTEFEUX)
        
        self.wait(56)
        soop.set_sync_pos_all()
        self.wait(12)
        soop.trigger_all()
        soop.reset_sync_pos_all()
        self.wait(14)
        soop.trigger_all()
    
    def vfs5_event(self, fsb: 'FsButton', fs_on: bool):
        soop = self.engine.modules['sooperlooper']
        
        if fsb is FsButton.FS_2 and fs_on:
            if self._tzou_drum_state is TzouDrumState.OFF:
                if START_MARKER is not Marker.DEBUT:
                    # soop.ask_loop_tempo(TZOU_DRUM)
                    return

                soop.sl(TZOU_DRUM, 'down', 'record')
                soop.demute(TZOU_DRUM)
                self._tzou_drum_state = TzouDrumState.REC
                self.engine.set_tempo(self.average_tempo)
                self.engine.start_cycle()
            
            elif self._tzou_drum_state is TzouDrumState.REC:
                soop.sl(TZOU_DRUM, 'up', 'record')
                soop.ask_loop_tempo(TZOU_DRUM)
        
        elif fsb is FsButton.FS_3 and fs_on:
            if START_MARKER is not Marker.DEBUT:
                soop.ask_loop_tempo(TZOU_DRUM)
                return
            
            self.engine.start_scene('la_chanson', self.la_chanson)
        
        elif fsb is FsButton.FS_4 and fs_on:
            self._tzou_drum_state = TzouDrumState.OFF
            soop = self.engine.modules['sooperlooper']
            soop.sl(TZOU_DRUM, 'hit', 'pause')
            soop.mute(TZOU_DRUM)
            self.change_tempo(self.average_tempo)

    def trigger_event(self):
        pass
        
    def loop_len_recv(self, loop_len: float):
        tempo = 60 / (loop_len / 4)
        while tempo > self.average_tempo * 1.5:
            tempo /= 2.0
        while tempo < self.average_tempo * 0.75:
            tempo *= 2.0
        
        self.change_tempo(tempo)
        
        if START_MARKER is not Marker.DEBUT:
            self.engine.start_scene('la_chanson', self.la_chanson)
        else:
            self.engine.start_cycle()
            
        
    def change_tempo(self, tempo: float):
        self.engine.set_tempo(tempo)
     
        carla = self.engine.modules['carla']
        carla.set_param_str('LSP Artistic Delay Stereo', 'Tempo 0', tempo)
        carla.set_param_str('Plujain-Ramp Live Aigu', 'Tempo', tempo)
        carla.set_param_str('Ramp GuitBass', 'Tempo', tempo)