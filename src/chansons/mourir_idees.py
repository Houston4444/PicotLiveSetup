from enum import auto
from chansons.orage import N_LOOPS
from chansons.song_parameters import SongParameters, scene_method, Marker, REPETTE


class Marker(Marker):
    DEBUT = auto()
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
SLIDE = 4
N_LOOPS = 5


class MourirIdees(SongParameters):
    average_tempo = 112
    seq_page = 12
    
    def __init__(self):
        super().__init__()
        self.scenes = [self.main_scene]
    
    def add_marker(self, marker: Marker):
        self._current_marker = marker
        
        if not REPETTE or marker is START_MARKER:
            self._repette_started = True
    
    def loop_sl(self, loop: int, updown: str, action: str):
        if REPETTE and not self._repette_started:
            return
        self.engine.modules['sooperlooper'].sl(loop, updown, action)
    
    @scene_method()
    def main_scene(self):
        print('allez vas y')
        
        self._repette_started = not REPETTE
        
        self.add_marker(Marker.DEBUT)

        seq192 = self.engine.modules['seq192']
        oscitronix = self.engine.modules['oscitronix']
        randomidi = self.engine.modules['randomidi']
        carla = self.engine.modules['carla']
        soop = self.engine.modules['sooperlooper']
        
        seq192.set_big_sequence(0)
        oscitronix.set_program('MourirSlide')
        
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 0.0)
        carla.set_param_str('InputGain', 'Gain', 1.0)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Wet amount', 0.2176)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Dry enable', 0.0)
        carla.set_param_str('TzouMagnetik', 'Output gain', 1.0)
        
        soop.set_n_loops(N_LOOPS)
        soop.send('/sl/-1/hit', 'pause')
        soop.reset_sync_pos_all()
        soop.mute_all()
        randomidi.start()
        soop.trigger_all()
        
        self.wait(16, 'beats')
        self.loop_sl(ALL, 'down', 'record')
        soop.demute(ARPEGE_TZOU)
        soop.demute(AIGUS)
        self.wait(72, 'beats')
        # carla.set_param_str('Plujain-Ramp Live Aigu', 'Double Speed', 1.0)
        carla.set_param_str('Plujain-Ramp Live Aigu', 'Division', 10.0)

        self.wait(14, 'beats')
        self.loop_sl(ALL, 'up', 'record')
        carla.set_param_str('Plujain-Ramp Live Aigu', 'Division', 6.0)
        # carla.set_param_str('Plujain-Ramp Live Aigu', 'Double Speed', 0.0)
        # passer sur Channel B (guitar)
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 1.0)
        
        self.add_marker(Marker.JUGEANT_QUIL)
        self.loop_sl(ALL, 'hit', 'trigger')
        
        self.wait(48, 'beats')
        self.loop_sl(BASSE, 'down', 'replace')
        soop.demute(BASSE)
        randomidi.stop()
        self.wait(38, 'beats')
        
        self.add_marker(Marker.SAINTS_JEANS)
        self.loop_sl(ARPEGE_TZOU, 'hit', 'trigger')
        
        print('SAINTS_JEANS')
        
        self.wait(48, 'beats')
        self.loop_sl(BASSE, 'up', 'replace')
        
        self.wait(24, 'beats')
        seq192.set_big_sequence(1)
        
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 0.0)
        carla.set_param_str('InputGain', 'Gain', 0.4)
        carla.set_param_str('LSP Artistic Delay Stereo', 'Wet amount', 0.1)
        
        self.wait(14, 'beats')
        
        self.add_marker(Marker.SACRIFICE)
        soop.trigger_all()        
        self.wait(16, 'beats')
        soop.trigger_all()

        self.loop_sl(RYTHME_TZOU, 'down', 'replace')
        soop.demute(RYTHME_TZOU)
        self.wait(16, 'beats')
        soop.set_sync_pos_all()
        
        print('SACRIFICE')
        
        self.wait(70, 'beats')
        self.loop_sl(RYTHME_TZOU, 'up', 'replace')
        
        self.add_marker(Marker.HECATOMBES)
        soop.trigger_all()
        soop.reset_sync_pos_all()
        self.wait(70, 'beats')
        
        self.add_marker(Marker.BOUTEFEUX)
        soop.trigger_all()
        
        self.wait(16, 'beats')
        soop.trigger_all() # 0
        
        self.wait(48, 'beats')
        carla.set_param_str('LSP Artistic Delay Stereo', 'Dry enable', 1.0)
        carla.set_param_str('TzouMagnetik', 'Output gain', 0.0)

        self.wait(24, 'beats')
        
        carla.set_param_str('LSP Artistic Delay Stereo', 'Dry enable', 0.0)
        carla.set_param_str('TzouMagnetik', 'Output gain', 1.0)
        
        soop.set_sync_pos_all()
        self.wait(12, 'beats') # 84
        soop.trigger_all() # 0
        soop.reset_sync_pos_all()
        self.wait(14, 'beats') #86
        