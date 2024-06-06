from rmodule import RModule
from songs import SONGS, Orage


class SooperLooper(RModule):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._loop = 0
        self._running_scene = ''
        
        self._demuted_loops = 0
        self._n_loops = 0

    def set_loop(self, loop: int):
        self._loop = loop

    def set_n_loops(self, n_loops: int):
        self._n_loops = n_loops

    def hit(self, action: str):
        self.send(f'/sl/{self._loop}/hit', action)
    
    def sl(self, loop: int, updown: str, action: str):
        # if REPETTE and not self._repette_started:
        #     return
        self.send(f'/sl/{loop}/{updown}', action)
  
    # def start_play_song(self):
    #     song = SONGS[self.engine.song_index]
        
    #     if isinstance(song, Orage):
    #         self._running_scene = 'orage_rec'
    #         # self.start_scene('orage_rec', self._orage_rec)
    #         self.start_scene('orage_rec', song.main_scene, self.engine)
    
    def stop_play_song(self):
        self.mute_all()

        if self._running_scene:
            self.stop_scene(self._running_scene)
            self._running_scene = ''
    
    def mute_all(self, kick=False):
        if kick:
            for i in range(self._n_loops):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].mute(f'Loop{i}')
            return
        
        self._demuted_loops = 0
        self.engine.modules['looper_volumes'].mute_all()

    def demute_all(self, kick=False):
        if kick:
            for i in range(self._n_loops):
                if self._demuted_loops & (2 ** i):
                    self.engine.modules['looper_volumes'].demute(f'Loop{i}')
            return

        self._demuted_loops = (2 ** self._n_loops) - 1
        self.engine.modules['looper_volumes'].demute_all()
    
    def mute(self, loop_n: int):
        self._demuted_loops &= ~ 2**loop_n
        self.engine.modules['looper_volumes'].mute(f'Loop{loop_n}')
        
    def demute(self, loop_n: int, volume=0.0):
        self._demuted_loops |= 2**loop_n
        self.engine.modules['looper_volumes'].demute(f'Loop{loop_n}', volume)
        
    def trigger_all(self):
        self.send('/sl/-1/hit', 'trigger')
    
    def set_sync_pos_all(self):
        self.send('/sl/-1/hit', 'set_sync_pos')
        
    def reset_sync_pos_all(self):
        self.send('/sl/-1/hit', 'reset_sync_pos')
