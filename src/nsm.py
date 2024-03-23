import os
from pathlib import Path
import json

from mentat import Module

class NsmClient(Module):
    def __init__(self, name: str, executable: str):
        NSM_URL = os.getenv('NSM_URL')
        if not NSM_URL:
            return
        
        try:
            server_port = int(NSM_URL.rpartition(':')[2][:-1])
        except:
            # TODO log something
            return

        super().__init__('nsm_client', protocol='osc', port=server_port)
        
        self.client_path = Path()

        # for auto-start compatibility, we save the NSM port in a file in /tmp
        tmp_path = Path('/tmp/el_mentator') / str(os.getpid())
        if not tmp_path.exists():
            tmp_path.mkdir(parents=True)

        tmp_file = str(tmp_path / 'nsm_port')
                
        already_started = True
        
        try:
            with open(tmp_file, 'r') as f:
                json_dict = json.load(f)
                assert json_dict['nsm_port'] == server_port
                self.client_path = Path(json_dict['client_path'])
        except:
            already_started = False
        
        if not already_started:
            self.send('/nsm/server/announce', name, '',
                      executable, 1, 0, os.getpid())
            
            with open(tmp_file, 'w') as f:
                f.write(json.dumps(
                    {'nsm_port': server_port, 'client_path': str(self.client_path)}))
    
    def _reply(self, address: str, err: int, msg: str):
        if err:
            self.send('/error', address, err, msg)
        else:
            self.send('/reply', address, msg)
    
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

    # functions you can re-implement
    def open(self, nsm_project: str, display_name: str,
             client_id: str) -> tuple[int, str]:
        return (0, 'Ready')
    
    def save(self) -> tuple[int, str]:
        return (0, 'Saved')
    