from enum import IntFlag, Enum
from typing import TYPE_CHECKING

from mentat import Module

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
    SOFTWARE_SWITCH = 1
    MULTIPLY = 2
    MUTE = 3
    TRIG = 4


class Vfs5Controls(Enum):
    SOOPERLOOPER = 1
    SEQ192_SEQUENCES = 2
    SONG = 3
    
    def next(self) -> 'Vfs5Controls':
        return Vfs5Controls(1 + self.value % 3)


class Leonardo(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        
        self._pressed_buttons = FsButton.NONE
        self._multi_action = MultiAction.NONE
        
        self._last_kick_hit = 0
        self._seq_playing = False
        
        self._vfs5_controls = Vfs5Controls.SEQ192_SEQUENCES
    
    def _vfs5_control_sooperlooper(self, fsb: FsButton, fs_on: bool):
        slp: 'SooperLooper' = self.engine.modules['sooperlooper']

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
    
    def _vfs5_control_sequences(self, fsb: FsButton, fs_on: bool):
        if not fs_on:
            return
        
        print('RIRIRI', fsb)
        
        seq192: 'Seq192' = self.engine.modules['seq192']
        
        if fsb is FsButton.FS_1:
            seq192.set_big_sequence(0)
        elif fsb is FsButton.FS_2:
            print('gros')
            seq192.set_big_sequence(1)
        elif fsb is FsButton.FS_3:
            seq192.set_big_sequence(2)
        elif fsb is FsButton.FS_4:
            seq192.set_big_sequence(3)
    
    def _vfs5_control_songs(self, fsb: FsButton, fs_on: bool):
        pass

    def _vfs5_control(self, cc_num: int, cc_value: int):
        fsb = FsButton(2 ** (cc_num - 90))
        fs_on = bool(cc_value > 63)

        print('zoeoof', fsb.name)

        if fs_on and fsb is not FsButton.FS_B:
            self._pressed_buttons |= fsb
        else:
            self._pressed_buttons &= ~fsb

        if fsb is FsButton.FS_B and self._pressed_buttons & FsButton.FS_4:
            self._vfs5_controls = self._vfs5_controls.next()
            self._multi_action = MultiAction.SOFTWARE_SWITCH
            return

        if self._vfs5_controls is Vfs5Controls.SOOPERLOOPER:
            self._vfs5_control_sooperlooper(fsb, fs_on)
        elif self._vfs5_controls is Vfs5Controls.SEQ192_SEQUENCES:
            self._vfs5_control_sequences(fsb, fs_on)
        elif self._vfs5_controls is Vfs5Controls.SONG:
            self._vfs5_control_songs(fsb, fs_on)
            
        if not self._pressed_buttons:
            self._multi_action = MultiAction.NONE

    def _kick_pressed(self, note_on: bool, note: int, velo: int):
        seq192: 'Seq192' = self.engine.modules['seq192']
        seq192.kick_pressed(note_on, note, velo)
    
    def route(self, address: str, args: list[int]):
        if address == '/control_change':
            channel, cc_num, cc_value = args
            
            if channel == 15 and 90 <= cc_num <= 94:
                self._vfs5_control(cc_num, cc_value)
        
        elif address in ('/note_on', '/note_off'):
            channel, note, velo = args
            
            if channel == 15 and note in (35, 36):
                self._kick_pressed(address == '/note_on', note, velo)
            