from enum import auto
from chansons.song_parameters import SongParameters, scene_method, Marker, REPETTE


class Marker(Marker):
    DEBUT = auto()
    TZOURAS_TIERCE = auto()
    TZOURAS_SKANKS = auto()
    CHANGE_INSTRU = auto()
    BASSE = auto()
    COUPLET2 = auto()
    COUPLET3 = auto()
    FRANKLIN = auto()
    SOLO_GUIT = auto()
    JUPITER = auto()
    NUAGES = auto()

    BONHOMME_MARI = auto()
    

START_MARKER = Marker.DEBUT


THEMES = 0
SKANKS = 1
AIGUS = 2
BASSE = 3
N_LOOPS = 4


class Orage(SongParameters):
    average_tempo = 140
    seq_page = 10
    vox_program = 'Orage Debut'
    stop_time = 3.528
    
    def __init__(self):
        super().__init__()
        self.scenes = [self.main_scene, self.derniers_couplets]
    
    
    
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
        '''scene method'''
        # la boucle fait

        # 0   8b : Gm

        # 8   8b : C

        # 16  8b: F

        # 24  8b: A7

        # 32  4b: Dm
        # 36  2b: E7
        # 38  2b: A7

        # 40  2b: Dm
        # 42  1b: Gm
        # 43  1b: C
        # 44  1b: F
        # 45  1b: A7
        # 46  2b: Dm
            
        self._repette_started = not REPETTE
        
        self.add_marker(Marker.DEBUT)

        seq192 = self.engine.modules['seq192']
        oscitronix = self.engine.modules['oscitronix']
        randomidi = self.engine.modules['randomidi']
        carla = self.engine.modules['carla']
        soop = self.engine.modules['sooperlooper']
        
        seq192.set_big_sequence(0)
        oscitronix.set_program('Orage Debut')        
        soop.set_n_loops(N_LOOPS)
        soop.send('/sl/-1/hit', 'pause')
        soop.mute_all()
        randomidi.start()

        # self.engine.set_cycle_length(1.0)
        self.wait(8, 'beats')

        ### BOUCLE mini theme Tzouras normal
        soop.trigger_all()
        self.loop_sl(THEMES, 'down', 'record')
        self.loop_sl(AIGUS, 'down', 'record')
        
        soop.demute(THEMES)
        soop.demute(AIGUS)

        self.wait(48, 'beats')
        
        while self._loop_louped:
            self.loop_sl(THEMES, 'down', 'record')
            self.loop_sl(AIGUS, 'down', 'record')
            self._loop_louped = False
            self.wait(48, 'beats')
        
        ### BOUCLE mini theme Tzouras tierce
        self.add_marker(Marker.TZOURAS_TIERCE)
        
        self.loop_sl(THEMES, 'down', 'overdub')
        self.loop_sl(AIGUS, 'down', 'overdub')

        self.wait(48, 'beats')
        
        while self._loop_louped:
            self.loop_sl(THEMES, 'down', 'overdub')
            self.loop_sl(AIGUS, 'down', 'overdub')
            self._loop_louped = False
            self.wait(48, 'beats')

        self.loop_sl(THEMES, 'up', 'overdub')
        self.loop_sl(AIGUS, 'up', 'overdub')

        ### BOUCLE avec skanks Tzouras
        self.add_marker(Marker.TZOURAS_SKANKS)
        self.loop_sl(SKANKS, 'down', 'record')        
        soop.demute(SKANKS)
        
        randomidi.stop()

        self.wait(24, 'beats')
        seq192.set_big_sequence(1)
        self.wait(24, 'beats')
        
        while self._loop_louped:
            self.loop_sl(SKANKS, 'up', 'record')
            self.loop_sl(SKANKS, 'down', 'record')
            self._loop_louped = False
            self.wait(48, 'beats')

        self.loop_sl(SKANKS, 'up', 'record')
        
        ### BOUCLE Changement d'instru
        self.add_marker(Marker.CHANGE_INSTRU)

        self.wait(24, 'beats')

        # passer sur Channel B (guitar)
        carla.set_param_str('ChannelB UseGuit', 'ChannelB', 1.0)

        self.wait(24, 'beats')
        
        ### BOUCLE Bass couplet 1 (parlez moi de la pluie)
        self.add_marker(Marker.BASSE)
        soop.trigger_all()
        self.loop_sl(BASSE, 'down', 'record')
        soop.demute(BASSE)
        self._loop_louped = False
        self.wait(48, 'beats')

        while self._loop_louped:
            self.loop_sl(BASSE, 'down', 'record')
            self._loop_louped = False
            self.wait(48, 'beats')

        self.loop_sl(BASSE, 'up', 'record')

        ### BOUCLE guitar couplet 2 (par un soir de novembre)
        self.add_marker(Marker.COUPLET2)

        carla.set_param_str('ChannelB bassguit', 'ChannelB', 1.0)

        self.wait(48, 'beats')
        
        ### BOUCLE guitar couplet 3 (je suis seule et j'ai peur)
        self.add_marker(Marker.COUPLET3)
        soop.trigger_all()
        self.wait(32, 'beats')
        soop.set_sync_pos_all()
        self.wait(16, 'beats')
        
        ### BOUCLE voix couplet 4 (en bénissant le nom de Benjamin Franklin)
        
        # petit pont sur Dm
        soop.trigger_all()
        soop.mute(THEMES)
        soop.mute(SKANKS)
        soop.mute(AIGUS)
        self.wait(4, 'beats')
        soop.send('/sl/-1/hit', 'trigger')
        self.wait(2, 'beats')
        soop.demute(AIGUS, 3.0)
        self.wait(2, 'beat')

        soop.reset_sync_pos_all()
        soop.trigger_all()
        
        self.add_marker(Marker.FRANKLIN)
        
        self.wait(48, 'beats')
        
        ### BOUCLE guitar solo
        self.add_marker(Marker.SOLO_GUIT)

        seq192.set_big_sequence(0)
        soop.demute(AIGUS)

        for i in range(24):
            if i % 2 and i != 23:
                soop.demute(THEMES)
            else:
                soop.mute(THEMES)

            self.wait(2, 'beat')
            if i == 20:
                seq192.set_big_sequence(1)
                soop.demute(SKANKS)

        soop.demute(AIGUS)
        
        ### Boucle Quand Jupiter
        self.add_marker(Marker.JUPITER)
        
        self.wait(24, 'beats')
        seq192.set_big_sequence(2)
        
        self.wait(14, 'beats')   #38
        soop.set_sync_pos_all()
        self.wait(2, 'beats')    #40
        soop.trigger_all() #38
        
        self.wait(3, 'beats')    #41
        seq192.set_big_sequence(3)
        oscitronix.set_program('Orage Funk')
        self.wait(5, 'beats')    #46
        soop.set_sync_pos_all()
        self.wait(2, 'beats')    #48 0
        soop.demute(THEMES)
        
        soop.trigger_all() # 46
        soop.reset_sync_pos_all()
        self.wait(2, 'beats')  #48 0
                
        ### BOUCLE guitar couplet 5 
        self.add_marker(Marker.NUAGES)
        
        self.wait(8, 'beats')
        soop.trigger_all()
        self.wait(8, 'beats')
        soop.trigger_all()
        
        self.wait(38, 'beats')
        soop.set_sync_pos_all()

        for nimp in range(16):
            self.wait(1, 'beats') # 40
            if nimp == 8:
                soop.mute(SKANKS)
            soop.trigger_all() # 38
        
        soop.reset_sync_pos_all()
        
        soop.mute_all()
        randomidi.stop()
    
    @scene_method()
    def derniers_couplets(self):
        self.add_marker(Marker.BONHOMME_MARI)
        
        seq192 = self.engine.modules['seq192']
        oscitronix = self.engine.modules['oscitronix']
        randomidi = self.engine.modules['randomidi']
        carla = self.engine.modules['carla']
        soop = self.engine.modules['sooperlooper']
        
        seq192.set_big_sequence(1)
        randomidi.start()
        soop.send('/sl/-1/hit', 'reset_sync_pos')
        soop.send('/sl/-1/hit', 'trigger')
        soop.mute_all()
        soop.demute(BASSE)
        # soop.demute(SKANKS)
        self.wait(24, 'beats')
        soop.demute(AIGUS)
        self.wait(8, 'beats')
        
        soop.send('/sl/-1/hit', 'set_sync_pos')
        self.wait(16, 'beats')
        
        soop.demute(AIGUS, 6.0)
        soop.send('/sl/-1/hit', 'trigger')
        self.wait(8, 'beats')
        
        soop.demute(SKANKS, -3.0)
        soop.send('/sl/-1/hit', 'trigger')
        self.wait(8, 'beats')
        
        soop.demute(THEMES)
        soop.send('/sl/-1/hit', 'trigger')
        soop.send('/sl/-1/hit', 'reset_sync_pos')
        self.wait(8, 'beats')
        # soop.demute(THEMES)
        self.wait(8, 'beats')
        
        # couplet final démarre sur Dm avec délai
        soop.mute_all()
        
    def set_loop_looped(self):
        super().set_loop_looped()
        
        if self._current_marker is Marker.DEBUT:
            self.loop_sl(THEMES, 'up', 'record')
            self.loop_sl(AIGUS, 'up', 'record')
            self.loop_sl(THEMES, 'hit', 'pause')
            self.loop_sl(AIGUS, 'hit', 'pause')
        
        elif self._current_marker is Marker.TZOURAS_TIERCE:
            self.loop_sl(THEMES, 'up', 'overdub')
            self.loop_sl(AIGUS, 'up', 'overdub')
            self.loop_sl(THEMES, 'hit', 'undo')
            self.loop_sl(AIGUS, 'hit', 'undo')
            
        elif self._current_marker is Marker.TZOURAS_SKANKS:
            self.loop_sl(SKANKS, 'up', 'record')
            self.loop_sl(SKANKS, 'hit', 'pause')
            
        elif self._current_marker is Marker.BASSE:
            self.loop_sl(BASSE, 'up', 'record')
            self.loop_sl(BASSE, 'hit', 'pause')
            