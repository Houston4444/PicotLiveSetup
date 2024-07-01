import subprocess
from typing import TYPE_CHECKING
import sys
import os
import signal
import logging
from leonardo import Vfs5Controls

from rmodule import RModule
from nsm import NsmClient
from songs import SONGS, SongParameters

if TYPE_CHECKING:
    from seq192 import Seq192
    from main_engine import MainEngine
    from carla import RegisterState


_logger = logging.getLogger(__name__)


class OptionalGui(RModule):    
    def __init__(self):
        super().__init__('optional_gui', protocol='osc', port=4324)
        
    def route(self, address: str, args: list):
        if not self.engine.modules['nsm_client'].gui_pid:
            return

        if address == '/raymentat/jarrive':
            self.send('/raymentat_gui/songs', *[str(song) for song in SONGS])
            self.send('/raymentat_gui/current_song', self.engine.song_index)
            self.send('/raymentat_gui/current_big_sequence',
                      self.engine.big_sequence)
            self.send('/raymentat_gui/all_vfs5_controls',
                      *[v.name for v in Vfs5Controls])
            self.send('/raymentat_gui/current_vfs5_control',
                      self.engine.modules['pedalboard'].get_vfs5_control_name())
            self.send('/raymentat_gui/carla_presets',
                      *self.engine.modules['carla'].list_presets())
            self.send('/raymentat_gui/carla_tcp_state',
                      self.engine.modules['carla'].get_tcp_connected_state().name)
            self.send('/raymentat_gui/tempo', self.engine.tempo)
            self.send('/raymentat_gui/toutestpret')

        elif address == '/raymentat/jepars':
            self.engine.modules['nsm_client']._send_gui_state(False)

        elif address == '/raymentat/change_song':
            song_index = args[0]
            if self.engine.song_index != song_index:
                self.engine.set_song(song_index)
                
        elif address == '/raymentat/change_big_sequence':
            big_sequence = args[0]
            if self.engine.big_sequence != big_sequence:
                self.engine.set_big_sequence(big_sequence)
        
        elif address == '/raymentat/change_vfs5_controls':
            for vfs5_controls in Vfs5Controls:
                if vfs5_controls.name == args[0]:
                    self.engine.modules['pedalboard'].change_vfs5_controls(
                        vfs5_controls)
                    break
        
        elif address == '/raymentat/save_carla_preset':
            self.engine.modules['carla'].save_preset(args[0])
            self.send('/raymentat_gui/carla_presets',
                      *self.engine.modules['carla'].list_presets())

    def set_song(self, song: SongParameters):
        self.send('/raymentat_gui/current_song',
                  int(self.engine.song_index))

    def set_big_sequence(self, big_sequence: int, force=False):
        self.send('/raymentat_gui/current_big_sequence', big_sequence)

    def set_vfs5_control(self, vfs5_controls: str):
        self.send('/raymentat_gui/current_vfs5_control', vfs5_controls)
        
    def set_carla_tcp_state(self, tcp_state: 'RegisterState'):
        self.send('/raymentat_gui/carla_tcp_state', tcp_state.name)

    def set_tempo(self, bpm: float):
        self.send('/raymentat_gui/tempo', bpm)

    def set_kick_velo(self, kick_velo: int):
        self.send('/raymentat_gui/last_kick_velo', kick_velo)


class NsmMentator(NsmClient):
    engine: 'MainEngine'
        
    def __init__(self):
        self.gui_pid = 0
        super().__init__(
            'ElMentator', 'el_mentator', ':optional-gui:monitor:')        
    
    def quit(self):
        self.save_tmp_file()
        self.hide_optional_gui()
    
    def save(self) -> tuple[int, str]:
        seq192: Seq192 = self.engine.modules['seq192']
        seq192.send('/status/extended')
        return (0, 'Saved')
    
    def open(self, nsm_project: str, display_name: str, 
             client_id: str) -> tuple[int, str]:
        self._start_brothers()
        return (0, 'Ready')
    
    def show_optional_gui(self):
        process = subprocess.Popen(
            ['python3', f'{sys.path[0]}/raymentat_gui.py'])
        self.gui_pid = process.pid
        self._send_gui_state(True)
    
    def hide_optional_gui(self):
        if self.gui_pid:
            os.kill(self.gui_pid, signal.SIGTERM)
            self.gui_pid = 0
        self._send_gui_state(False)
        
    def _start_brothers(self):
        for brother_id, brother in self.brothers.items():
            if brother_id == 'hydrogen' and not brother.is_running():
                subprocess.run(['ray_control', 'client', 'hydrogen', 'start'],
                               capture_output=True)
                break    

            elif brother_id == 'Carla_7' and brother.is_running():
                self.engine.modules['carla'].register_tcp()
                break
        
    def brother_event(self, client_id: str, event: str):
        if client_id == 'hydrogen' and event == 'ready':
            rayc_proc = subprocess.run(
                ['ray_control', 'list_clients', 'auto_start'],
                capture_output=True, text=True)

            if rayc_proc.returncode:
                _logger.error('ray_control list_clients failed.')
                return

            brother_ids = rayc_proc.stdout.splitlines()
            for brother_id in brother_ids:
                if brother_id == 'el_mentato':
                    continue

                if brother_id in ('Mixette', 'xtuner'):
                    continue

                if self.brothers[brother_id].is_running():
                    continue
                
                subprocess.run(
                    ['ray_control', 'client', brother_id, 'start'],
                    capture_output=True)

        elif client_id == 'Carla_7':
            if event == 'ready':
                self.engine.modules['carla'].register_tcp()

            elif event in ('stopped_by_server', 'stopped_by_itself',
                           'removed', 'stop_request'):
                self.engine.modules['carla'].unregister_tcp()
                
    def monitor_client_states_finished(self):
        carla_broth = self.brothers['Carla_7']
        if carla_broth.is_running():
            self.engine.modules['carla'].register_tcp()