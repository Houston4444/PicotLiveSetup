from rmodule import RModule
from songs import SONGS, Orage, SongParameters

REPETTE = True

THEMES = 0
SKANKS = 1
AIGUS = 2
BASSE = 3


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
        
        ALL = -1
        
        
        print('orage start')
        
        seq192 = self.engine.modules['seq192']
        seq192.set_big_sequence(0)
        self._repette_started = False
        # self._start_repette()
        self._demute_allowed = False
        
        

        self.mute_all()
        self.engine.modules['randomidi'].start()
        self.send('/sl/-1/hit', 'pause')
        self.wait(8, 'beats')

        ### BOUCLE mini theme Tzouras normal
        self.sl(THEMES, 'down', 'record')
        self.sl(AIGUS, 'down', 'record')
        
        self.demute(THEMES)
        self.demute(AIGUS)

        self.wait(48, 'beats')
        
        ### BOUCLE mini theme Tzouras tierce
        self.sl(THEMES, 'down', 'overdub')
        self.sl(AIGUS, 'down', 'overdub')

        self.wait(48, 'beats')

        self._demute_allowed = True

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
        self.sl(BASSE, 'up', 'record')
        self.engine.modules['carla'].send_param(10, 0, 1.0)

        self.wait(48, 'beats')
        
        ### BOUCLE guitar couplet 3 (je suis seule et j'ai peur)
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
        self.demute(AIGUS)
        self.wait(2, 'beat')

        self.send('/sl/-1/hit', 'reset_sync_pos')
        self.send('/sl/-1/hit', 'trigger')
        
        self.wait(48, 'beats')
        
        ### BOUCLE guitar solo
        self._start_repette()
        # self._start_repette()
        seq192.set_big_sequence(0)
        # self.wait(48, 'beats')
        for i in range(24):
            if i % 2:
                self.demute(THEMES)
            else:
                self.mute(THEMES)
                
            self.wait(2, 'beat')
            if i == 20:
                seq192.set_big_sequence(2)
        
        self.demute(SKANKS)
        self.demute(AIGUS)
        
        ### Boucle Quand Jupiter
        self.wait(48, 'beats')
        self.demute(THEMES)
        
        ### BOUCLE guitar couplet 5 
        
        for i in range(10):
            self.wait(48, 'beats')
            self.send('/sl/-1/hit', 'trigger')
            print('hop new chillle')
        
        self.mute_all()
        self._running_scene = ''
        self._demute_allowed = False
        self.engine.modules['randomidi'].stop()
        self.engine.modules['carla'].send_param(7, 0, 0.0)
        
    def start_play_song(self):
        if isinstance(SONGS[self.engine.song_index], Orage):
            self._running_scene = 'orage_rec'
            self.start_scene('orage_rec', self._orage_rec)
    
    def stop_play_song(self):
        self.mute_all()
        self._demute_allowed = False

        if self._running_scene:
            self.stop_scene(self._running_scene)
            self._running_scene = ''
    
    def mute_all(self, kick=False):
        print('SOOP MUTE ALL')
        if kick:
            for i in range(4):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].mute(f'Loop{i}')
            return
        
        # self.send('/sl/-1/down', 'mute')
        self._demuted_loops = 0
        self.engine.modules['looper_volumes'].mute_all()

    def demute_all(self, kick=False):
        print('SOOP DEMUTE ALL')
        if kick:
            for i in range(4):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].demute(f'Loop{i}')
            return

        self._demuted_loops = 15
        self.engine.modules['looper_volumes'].demute_all()
    
    def mute(self, loop_n: int):
        print('mute___av', loop_n, self._demuted_human())
        self._demuted_loops &= ~ 2**loop_n
        print('mute___ap', loop_n, self._demuted_human())
        self.engine.modules['looper_volumes'].mute(f'Loop{loop_n}')
        
    def demute(self, loop_n: int):
        print('demute_av', loop_n, self._demuted_human())
        self._demuted_loops |= 2**loop_n
        print('demute_ap', loop_n, self._demuted_human())
        self.engine.modules['looper_volumes'].demute(f'Loop{loop_n}')
        
    def _demuted_human(self) -> str:
        ret = ''
        for i in range(4):
            if self._demuted_loops & (2**i):
                ret += '1'
            else:
                ret += '0'
        return ret