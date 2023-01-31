from enum import IntFlag, Enum
from typing import TYPE_CHECKING
import time

from mentat import Module, Engine

if TYPE_CHECKING:
    from sooperlooper import SooperLooper
    from seq192 import Seq192


class FsButton(IntFlag):
    NONE = 0x00
    FS_B = 0x01
    FS_1 = 0x02
    FS_2 = 0x04
    FS_3 = 0x08
    FS_4 = 0x10


class MultiAction(Enum):
    NONE = 0
    MULTIPLY = 1
    MUTE = 2
    TRIG = 3
    

class Leonardo(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._pressed_buttons = FsButton.NONE
        self._multi_action = MultiAction.NONE
        
        self._last_kick_hit = 0
    
    def _vfs5_control_sooperlooper(self, cc_num: int, cc_value: int):
        engine = Engine.INSTANCE
        slp: 'SooperLooper' = engine.modules['sooperlooper']
        fsb = FsButton(2 ** (cc_num - 90))
        fs_on = bool(cc_value > 63)

        if cc_value > 63 and fsb is not FsButton.FS_B:
            self._pressed_buttons |= fsb
        else:
            self._pressed_buttons &= ~fsb

        if fsb is FsButton.FS_B:
            slp.set_loop(1 if fs_on else 0)

        if fsb is FsButton.FS_1:
            if self._pressed_buttons is FsButton.FS_1:
                slp.hit('record')
            
            elif self._pressed_buttons is FsButton.FS_1|FsButton.FS_4:
                slp.hit('trigger')
                self._multi_action = MultiAction.TRIG

        elif fsb is FsButton.FS_2:
            if self._multi_action is MultiAction.NONE:
                if self._pressed_buttons in (FsButton.NONE, FsButton.FS_2):
                    slp.hit('overdub')
                                    
                elif self._pressed_buttons is FsButton.FS_2|FsButton.FS_3:
                    slp.hit('multiply')
                    self._multi_action = MultiAction.MULTIPLY

            elif self._multi_action is MultiAction.MULTIPLY:
                if self._pressed_buttons is FsButton.NONE:
                    slp.hit('multiply')

        elif fsb is FsButton.FS_3:
            if self._multi_action is MultiAction.NONE:
                if self._pressed_buttons is FsButton.NONE:
                    slp.hit('undo')
                elif self._pressed_buttons is FsButton.FS_2|FsButton.FS_3:
                    slp.hit('multiply')
                    self._multi_action = MultiAction.MULTIPLY
                elif self._pressed_buttons is FsButton.FS_3|FsButton.FS_4:
                    slp.hit('mute')
                    self._multi_action = MultiAction.MUTE

            elif self._multi_action is MultiAction.MULTIPLY:
                if self._pressed_buttons is FsButton.NONE:
                    slp.hit('multiply')

        elif fsb is FsButton.FS_4:
            if self._multi_action is MultiAction.NONE:
                if self._pressed_buttons is FsButton.NONE:
                    slp.hit('redo')
                elif self._pressed_buttons is FsButton.FS_3|FsButton.FS_4:
                    slp.hit('mute')
                    self._multi_action = MultiAction.MUTE
            
        if not self._pressed_buttons:
            self._multi_action = MultiAction.NONE
    
    def _kick_pressed(self, note_on: bool, note: int, velo: int):
        engine = Engine.INSTANCE
        seq192: 'Seq192' = engine.modules['seq192']

        if note_on:
            kick_time = time.time()
            duration = kick_time - self._last_kick_hit
            if duration < 2.0:
                seq192.set_tempo(60 / duration)
                seq192.start()
            else:
                self._last_kick_hit = kick_time
    
    def route(self, address: str, args: list):
        print('qpofgg', address, args)
        if address == '/control_change':
            channel: int
            cc_num: int
            cc_value: int
            
            channel, cc_num, cc_value = args
            
            if channel == 15 and 90 <= cc_num <= 94:
                self._vfs5_control_sooperlooper(cc_num, cc_value)
        
        elif address in ('/note_on', '/note_off'):
            channel: int
            note: int
            velo: int
            
            channel, note, velo = args
            
            if channel == 15 and note in (35, 36):
                self._kick_pressed(address == '/note_on', note, velo)
            