
from re import S
from threading import Timer
from typing import Union
from mentat import Module
from enum import IntEnum

OPEN_TIME = 0.150 # ms, durée d'ouverture de la pédale appuyée

class Mute(IntEnum):
    NONE = 0
    MUTE_WAIT = 1
    MUTE = 2
    

class Param(IntEnum):
    KICK_SPACING = 0
    MUTE = 1
    VELO_1 = 2


class CarlaMultip(Module):
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        self._mute_timer = Timer(0.150, self._mute)
        self._muted = False
        self._waiting_demute = False
    
    def _send_pg(self, param_index: int, value: Union[str, bool, int, float]):
        self.send('/Carla_Multi_Client_multip/0/set_parameter_value',
                  param_index, float(value))
        
        # param_name: str
        # if param_index == Param.KICK_SPACING:
        #     param_name = "Double%20Kick%20allowed"
        # elif param_index == Param.MUTE:
        #     param_name = "Mute"
        # else:
        #     param_name = "Velocity%201"
        # self.send('Non-Mixer-XT.m_xt/strip/flako/Plujain-Multipmidi/' + param_name + '/unscaled',
        #           float(value))
    
    def _mute(self):
        self._send_pg(Param.MUTE, Mute.MUTE)
        self._muted = True

        self._remake_mute_timer()
    
    def _remake_mute_timer(self):
        del self._mute_timer
        self._mute_timer = Timer(0.150, self._mute)

    def _velo_map(self, velo: int, mini=0, maxi=127) -> int:
        return mini + int((velo/127) * (maxi - mini))

    def kick_pressed(self, note_on: bool, note: int, velo: int):
        if note_on:
            self._send_pg(Param.VELO_1, self._velo_map(velo, 30, 127))
            if not self._muted:
                self._mute_timer.start()
        else:
            if self._muted:
                self._waiting_demute = True
                self._send_pg(Param.MUTE, Mute.MUTE_WAIT)
                # self._send_pg(Param.MUTE, False)
            self._mute_timer.cancel()
            self._remake_mute_timer()
            self._muted = False
                        
    def demute(self, force=False):
        if not force and not self._waiting_demute:
            return
        
        self._send_pg(Param.MUTE, False)
        self._muted = False
        self._waiting_demute = False