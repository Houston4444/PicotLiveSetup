import os
from pathlib import Path
import json
from typing import Any
import logging

from mentat import Module

_logger = logging.getLogger(__name__)
    

class BrotherClient:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.jack_client_name = ''
        self.started_at_start = False
        self.last_event = ''
        
    def is_running(self) -> bool:
        if not self.last_event:
            return self.started_at_start
        
        if self.last_event in (
                'started', 'joined', 'ready', 'saved',
                'switched_to', 'open_error', 'save_error',
                'save_request', 'stop_request'):
            return True
        return False
    
    def as_dict(self) -> dict:
        return {'jack_client_name': self.jack_client_name,
                'started_at_start': self.started_at_start,
                'last_event': self.last_event}
        
    def from_dict(self, client_id: str, brodict: dict) -> 'BrotherClient':
        brother = BrotherClient(client_id)
        brother.jack_client_name = brodict['jack_client_name']
        brother.started_at_start = brodict['started_at_start']
        brother.last_event = brodict['last_event']
        return brother


class NsmClient(Module):
    def __init__(self, nsm_name: str, executable: str, capabilities: str):
        self.nsm_name = nsm_name
        self.executable = executable
        self.capabilities = capabilities

        self.client_path = Path()
        self.brothers = dict[str, BrotherClient]()
        
        NSM_URL = os.getenv('NSM_URL')
        if not NSM_URL:
            _logger.error('NsmClient started without NSM_URL environment variable')
            return
        
        try:
            server_port = int(NSM_URL.rpartition(':')[2][:-1])
        except BaseException as e:
            _logger.error(str(e))
            return

        super().__init__('nsm_client', protocol='osc', port=server_port)

        # for auto-start compatibility, we save the NSM port in a file in /tmp
        tmp_path = Path('/tmp/el_mentator') / str(os.getpid())
        if not tmp_path.exists():
            tmp_path.mkdir(parents=True)

        self._tmp_file = str(tmp_path / 'nsm_port')
                
        already_started = True
        
        try:
            with open(self._tmp_file, 'r') as f:
                json_dict = json.load(f)
                assert json_dict['nsm_port'] == self.port
                self.client_path = Path(json_dict['client_path'])
        except:
            already_started = False
        
        if already_started:
            self.send('/nsm/server/monitor_reset')
        else:        
            self.send('/nsm/server/announce', self.nsm_name,
                      self.capabilities, self.executable, 1, 0, os.getpid())
                
            with open(self._tmp_file, 'w') as f:
                f.write(json.dumps(
                    {'nsm_port': self.port,
                     'client_path': str(self.client_path)}))
    
    def save_tmp_file(self):
        with open(self._tmp_file, 'w') as f:
            brothers_dict = {}
            for brother_id, brother in self.brothers.items():
                brothers_dict[brother_id] = brother.as_dict()

            f.write(json.dumps(
                {'nsm_port': self.port,
                 'client_path': str(self.client_path),
                 'brothers': brothers_dict}))
    
    def _reply(self, address: str, err: int, msg: str):
        if err:
            self.send('/error', address, err, msg)
        else:
            self.send('/reply', address, msg)
    
    def _send_gui_state(self, visible: bool):
        if visible:
            self.send('/nsm/client/gui_is_shown')
        else:
            self.send('/nsm/client/gui_is_hidden')
    
    def route(self, address: str, args: list):        
        if address == '/reply':
            reply_path = args.pop(0)
            if reply_path == '/nsm/server/announce':
                message, sm_name, server_capabilities = args
        
        elif address == '/nsm/client/open':
            if args and isinstance(args[0], str):
                self.client_path = Path(args[0])
            self._reply(address, *self.open(*args))
        
        elif address == '/nsm/client/save':
            self._reply(address, *self.save())
            
        elif address == '/nsm/client/show_optional_gui':
            self.show_optional_gui()
        
        elif address == '/nsm/client/hide_optional_gui':
            self.hide_optional_gui()
        
        elif address == '/nsm/client/monitor/client_state':
            client_id, jack_client_name, is_started = args
            if not client_id:
                self.monitor_client_states_finished()
                return
            
            brother = BrotherClient(client_id)
            brother.jack_client_name = jack_client_name
            brother.started_at_start = bool(is_started)            
            self.brothers[client_id] = brother
        
        elif address == '/nsm/client/monitor/client_event':
            client_id, event = args
            brother = self.brothers.get(client_id)
            if brother is None:
                brother = BrotherClient(client_id)
                self.brothers[client_id] = brother

            brother.last_event = event
            self.brother_event(client_id, event)

    # functions you can re-implement
    def open(self, nsm_project: str, display_name: str,
             client_id: str) -> tuple[int, str]:
        return (0, 'Ready')
    
    def save(self) -> tuple[int, str]:
        return (0, 'Saved')
    
    def show_optional_gui(self):
        ...
    
    def hide_optional_gui(self):
        ...
    
    def brother_event(self, client_id: str, event: str):
        ...
    
    def monitor_client_states_finished(self):
        ...