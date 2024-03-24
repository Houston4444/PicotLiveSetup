import subprocess
from typing import TYPE_CHECKING
import sys
import os
import signal
import logging

from mentat import Module
from nsm import NsmClient
from songs import SONGS, SongParameters

if TYPE_CHECKING:
    from seq192 import Seq192
    from main_engine import MainEngine


_logger = logging.getLogger(__name__)


class OptionalGui(Module):
    def __init__(self):
        super().__init__('optional_gui', protocol='osc', port=4324)
        
    def route(self, address: str, args: list):
        print('mssmdoptional gui', address, args)
        
        if address == '/raymentat/jarrive':
            self.send('/raymentat_gui/songs', *[str(song) for song in SONGS])
            self.send('/raymentat_gui/current_song', self.engine._song_index)
        
        elif address == '/raymentat/jepars':
            self.engine.modules['nsm_client']._send_gui_state(False)
    
    def set_song(self, song: SongParameters):
        self.send('/raymentat_gui/current_song',
                  int(self.engine._song_index))


class NsmMentator(NsmClient):
    engine: 'MainEngine'
    
    def __init__(self):
        super().__init__(
            'ElMentator', 'el_mentator', ':optional-gui:monitor:')        
        self.gui_pid = 0
        self.song = None
    
    def set_song(self, song: SongParameters):
        self.song = song
    
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
        self._send_gui_state(False)
        
    def _start_brothers(self):
        subprocess.run(['ray_control', 'client', 'hydrogen', 'start'],
                       capture_output=True)
        
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

                if self.brothers[brother_id].is_running():
                    continue
                
                subprocess.run(
                    ['ray_control', 'client', brother_id, 'start'],
                    capture_output=True)

        elif client_id == 'Carla_7':
            if event == 'ready':
                self.engine.modules['carla'].start_osc_tcp()

            elif event in ('stopped_by_server', 'stopped_by_itself',
                           'removed', 'stop_request'):
                self.engine.modules['carla'].stop_osc_tcp()
                
        