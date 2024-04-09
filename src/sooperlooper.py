from rmodule import RModule
from songs import SONGS, Orage

class SooperLooper(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._loop = 0
        self._running_scene = ''
        self._demute_allowed = False
    
    def set_loop(self, loop: int):
        self._loop = loop

    def hit(self, action: str):
        self.send(f'/sl/{self._loop}/hit', action)
    
    def _orage_rec(self):
        '''scene method'''
        # self.engine.modules['carla'].off_ramps(True)
        self._demute_allowed = False

        self.mute_all()
        self.wait(8, 'beats')
        self.send('/sl/0/down', 'record')
        self.send('/sl/2/down', 'record')
        self.demute(0)
        self.demute(2)

        self.wait(48, 'beats')
        self.send('/sl/0/up', 'record')
        self.send('/sl/2/up', 'record')
        self.send('/sl/1/down', 'record')
        self.demute(1)
        
        self.engine.modules['randomidi'].stop()
        # self.engine.modules['carla'].off_ramps(False)

        self.wait(48, 'beats')
        self.send('sl/1/up', 'record')
        self.send('/sl/-1/hit', 'trigger')
        # self.send('/sl/1/hit', 'trigger')
        
        self._demute_allowed = True
        
        for i in range(10):
            self.wait(48, 'beats')
            self.send('/sl/-1/hit', 'trigger')
            print('hop new chillle')
        
        self.mute_all()
        self._running_scene = ''
        
    def start_play_song(self):
        if isinstance(SONGS[self.engine.song_index], Orage):
            self._running_scene = 'orage_rec'
            self.start_scene('orage_rec', self._orage_rec)
    
    def stop_play_song(self):
        self.mute_all()

        if self._running_scene:
            self.stop_scene(self._running_scene)
            self._running_scene = ''
    
    def mute_all(self):
        print('SOOP MUTE ALL')
        # self.send('/sl/-1/down', 'mute')
        self.engine.modules['looper_volumes'].mute_all()

    def demute_all(self):
        print('SOOP DEMUTE ALL')
        if self._demute_allowed:
            print('SOOP DEMUTE ALL OK')
            # self.send('/sl/-1/up', 'mute')
            self.engine.modules['looper_volumes'].demute_all()
    
    def mute(self, loop_n: int):
        self.engine.modules['looper_volumes'].mute(f'Loop{loop_n}')
        
    def demute(self, loop_n: int):
        self.engine.modules['looper_volumes'].demute(f'Loop{loop_n}')