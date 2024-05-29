from enum import Enum, auto

from rmodule import RModule
from songs import SONGS, Orage, SongParameters

REPETTE = True

class Marker(Enum):
    DEBUT = auto()
    CHANGE_INSTRU = auto()
    COUPLET2 = auto()
    COUPLET3 = auto()
    FRANKLIN = auto()
    SOLO_GUIT = auto()
    JUPITER = auto()
    NUAGES = auto()
    

START_MARKER = Marker.CHANGE_INSTRU

THEMES = 0
SKANKS = 1
AIGUS = 2
BASSE = 3
N_LOOPS = 4


class SooperLooper(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._loop = 0
        self._running_scene = ''
        self._demute_allowed = False
        self._repette_started = False
        self._demuted_loops = 0
    
    def wait(self, *args):
        if REPETTE and not self._repette_started:
            return
        super().wait(*args)

    def add_marker(self, marker: Marker):
        if REPETTE and marker is START_MARKER:
            self._repette_started = True

    def set_loop(self, loop: int):
        self._loop = loop

    def set_song(self, song: SongParameters):
        # return super().set_song(song)
        self.mute_all(kick=True)

    def _start_repette(self):
        self._repette_started = True

    def hit(self, action: str):
        self.send(f'/sl/{self._loop}/hit', action)
    
    def sl(self, loop: int, updown: str, action: str):
        if REPETTE and not self._repette_started:
            return
        self.send(f'/sl/{loop}/{updown}', action)
    
    def _orage_rec(self):
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
        
        
        print('orage start')
        self._repette_started = not REPETTE
        
        self.add_marker(Marker.DEBUT)

        seq192 = self.engine.modules['seq192']
        seq192.set_big_sequence(0)
        self.engine.modules['oscitronix'].set_program('Orage Debut')

        self.mute_all()
        self.engine.modules['randomidi'].start()
        self.wait(8, 'beats')

        ### BOUCLE mini theme Tzouras normal
        self.send('/sl/-1/hit', 'trigger')
        self.sl(THEMES, 'down', 'record')
        self.sl(AIGUS, 'down', 'record')
        
        self.demute(THEMES)
        self.demute(AIGUS)

        self.wait(48, 'beats')
        
        ### BOUCLE mini theme Tzouras tierce
        self.sl(THEMES, 'down', 'overdub')
        self.sl(AIGUS, 'down', 'overdub')

        self.wait(48, 'beats')

        ### BOUCLE avec skanks Tzouras
        self.sl(THEMES, 'up', 'overdub')
        self.sl(AIGUS, 'up', 'overdub')
        self.sl(SKANKS, 'down', 'record')        
        self.demute(SKANKS)
        
        self.engine.modules['randomidi'].stop()

        # self.wait(48, 'beats')
        self.wait(24, 'beats')
        seq192.set_big_sequence(1)
        self.wait(24, 'beats')

        self.sl(SKANKS, 'up', 'record')
        
        ### BOUCLE Changement d'instru
        self.add_marker(Marker.CHANGE_INSTRU)

        self.wait(24, 'beats')
        # passer sur Channel B (guitar)
        self.engine.modules['carla'].send_param(7, 0, 1.0)

        self.wait(24, 'beats')
        
        ### BOUCLE Bass couplet 1 (parlez moi de la pluie)
        self.send('/sl/-1/hit', 'trigger')
        self.sl(BASSE, 'down', 'record')
        self.demute(BASSE)
        self.wait(48, 'beats')

        ### BOUCLE guitar couplet 2 (par un soir de novembre)
        self.add_marker(Marker.COUPLET2)
        self.sl(BASSE, 'up', 'record')

        self.engine.modules['carla'].send_param(10, 0, 1.0)

        self.wait(48, 'beats')
        
        ### BOUCLE guitar couplet 3 (je suis seule et j'ai peur)
        self.add_marker(Marker.COUPLET3)
        self.send('/sl/-1/hit', 'trigger')
        self.wait(32, 'beats')
        self.send('/sl/-1/hit', 'set_sync_pos')
        self.wait(16, 'beats')
        
        ### BOUCLE voix couplet 4 (en bénissant le nom de Benjamin Franklin)
        
        # petit pont sur Dm
        self.send('/sl/-1/hit', 'trigger')
        self.mute(THEMES)
        self.mute(SKANKS)
        self.mute(AIGUS)
        self.wait(4, 'beats')
        self.send('/sl/-1/hit', 'trigger')
        self.wait(2, 'beats')
        self.demute(AIGUS, 3.0)
        self.wait(2, 'beat')

        self.send('/sl/-1/hit', 'reset_sync_pos')
        self.send('/sl/-1/hit', 'trigger')
        
        self.add_marker(Marker.FRANKLIN)
        
        self.wait(48, 'beats')
        
        ### BOUCLE guitar solo
        self.add_marker(Marker.SOLO_GUIT)

        seq192.set_big_sequence(0)
        self.demute(AIGUS)

        for i in range(24):
            if i % 2 and i != 23:
                self.demute(THEMES)
            else:
                self.mute(THEMES)

            self.wait(2, 'beat')
            if i == 20:
                seq192.set_big_sequence(1)
                self.demute(SKANKS)

        self.demute(AIGUS)
        
        ### Boucle Quand Jupiter
        self.add_marker(Marker.JUPITER)
        
        self.wait(12, 'beats')
        seq192.set_big_sequence(2)
        self.wait(11, 'beats')
        seq192.set_big_sequence(3)
        self.engine.modules['oscitronix'].set_program('Orage Funk')
        # self.demute(SKANKS)
        self.wait(25, 'beats')
        self.demute(THEMES)
        
        ### BOUCLE guitar couplet 5 
        self.add_marker(Marker.NUAGES)
        
        for i in range(10):
            self.wait(48, 'beats')
            self.send('/sl/-1/hit', 'trigger')
            print('hop new chillle')
        
        self.mute_all()
        self._running_scene = ''
        self.engine.modules['randomidi'].stop()
        self.engine.modules['carla'].send_param(7, 0, 0.0)
        
    def start_play_song(self):
        if isinstance(SONGS[self.engine.song_index], Orage):
            self._running_scene = 'orage_rec'
            self.start_scene('orage_rec', self._orage_rec)
    
    def stop_play_song(self):
        self.mute_all()

        if self._running_scene:
            self.stop_scene(self._running_scene)
            self._running_scene = ''
    
    def mute_all(self, kick=False):
        if kick:
            for i in range(N_LOOPS):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].mute(f'Loop{i}')
            return
        
        self._demuted_loops = 0
        self.engine.modules['looper_volumes'].mute_all()

    def demute_all(self, kick=False):
        if kick:
            for i in range(N_LOOPS):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].demute(f'Loop{i}')
            return

        self._demuted_loops = (2 ** N_LOOPS) - 1
        self.engine.modules['looper_volumes'].demute_all()
    
    def mute(self, loop_n: int):
        self._demuted_loops &= ~ 2**loop_n
        self.engine.modules['looper_volumes'].mute(f'Loop{loop_n}')
        
    def demute(self, loop_n: int, volume=0.0):
        self._demuted_loops |= 2**loop_n
        self.engine.modules['looper_volumes'].demute(f'Loop{loop_n}', volume)
