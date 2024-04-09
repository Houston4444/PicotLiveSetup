
from email.policy import default
from enum import IntEnum
from re import S
from typing import TYPE_CHECKING, Any
import time
import threading
import logging
import json
import liblo
import os
from pathlib import Path


from rmodule import RModule
from songs import MourirIdees, SongParameters, Orage

if TYPE_CHECKING:
    from main_engine import MainEngine

_logger = logging.getLogger(__name__)


class RegisterState(IntEnum):
    NO = 0
    NOT_SURE = 1
    YES = 2
    

class Param:
    symbol: str
    name: str
    is_output: bool
    default: float
    value: float
    
    def __init__(self):
        self.symbol = ''
        self.name = ''
        self.is_output = False
        self.default = 0.0
        self.value = float('nan')


class Plugin:
    def __init__(self):
        self.name = ''
        self.label = ''
        self.is_active = True
        self.volume = 1.0
        self.drywet = 1.0
        self.n_param = 0
        self.params = dict[int, Param]()


class EngineCallback(IntEnum):
    DEBUG = 0
    PLUGIN_ADDED = 1
    PLUGIN_REMOVED = 2
    PLUGIN_RENAMED = 3
    PLUGIN_UNAVAILABLE = 4
    PARAMETER_VALUE_CHANGED = 5
    PARAMETER_DEFAULT_CHANGED = 6
    PARAMETER_MAPPED_CONTROL_INDEX_CHANGED = 7
    PARAMETER_MIDI_CHANNEL_CHANGED = 8
    OPTION_CHANGED = 9
    PROGRAM_CHANGED = 10
    MIDI_PROGRAM_CHANGED = 11
    UI_STATE_CHANGED = 12
    NOTE_ON = 13
    NOTE_OFF = 14
    UPDATE = 15
    RELOAD_INFO = 16
    RELOAD_PARAMETERS = 17
    RELOAD_PROGRAMS = 18
    RELOAD_ALL = 19
    PATCHBAY_CLIENT_ADDED = 20
    
    
class _OscTcpServer(liblo.ServerThread):
    def __init__(self, parent: 'Carla') -> None:
        super().__init__(8755, liblo.TCP)
        self.parent = parent
        self.carla_addr = liblo.Address('127.0.0.1', 19998, liblo.TCP)
        self.PREPATH = '/Carla_Multi_Client_Carla_7'
        self.plugins = list[Plugin]()
        self.register_state = RegisterState.NO

    def _get_register_url(self) -> str:
        return f'osc.tcp://127.0.0.1:{self.port}/ctrl'

    def _set_tcp_connected_state(self, tcp_state: RegisterState):
        if tcp_state is self.register_state:
            return

        self.register_state = tcp_state
        print('yaromzek', self.register_state)
        self.parent.set_tcp_connected_state(tcp_state)

    def register(self):
        self.carla_send('/unregister', self._get_register_url())
        self.carla_send('/register', self._get_register_url())
        self._set_tcp_connected_state(RegisterState.NOT_SURE)

    def unregister(self):
        self.carla_send('/unregister', self._get_register_url())
        self._set_tcp_connected_state(RegisterState.NO)
        # time.sleep(0.005)
        # super().stop()
        # time.sleep(0.005)
        # self.free()
        # time.sleep(0.005)

    def stop(self):
        super().stop()
        time.sleep(0.005)
        self.free()
        time.sleep(0.005)

    def carla_send(self, *args):
        self.send(self.carla_addr, *args)

    def set_tempo(self, bpm: float):
        self.carla_send('/ctrl/transport_bpm', 0, float(bpm))
        time.sleep(0.0054)

    def save_preset(self, preset_path: Path, full=False):
        out_list = list[dict[str, Any]]()
            
        for plugin in self.plugins:
            params_dict = {}
            pg_dict = {'name': plugin.name,
                       'label': plugin.label,
                       'is_active': plugin.is_active,
                       'volume': plugin.volume,
                       'drywet': plugin.drywet,
                       'n_param': plugin.n_param,
                       'params': params_dict}
            
            if full:
                for pm_index, param in plugin.params.items():
                    if not param.is_output:
                        params_dict[pm_index] = {
                            'name': param.name,
                            'def': param.default,
                            'value': param.value}
            else:            
                for pm_index, param in plugin.params.items():
                    if param.default != param.value and not param.is_output:
                        params_dict[pm_index] = {
                            'name': param.name,
                            'def': param.default,
                            'value': param.value}

            out_list.append(pg_dict)
        
        preset_path.parent.mkdir(exist_ok=True, parents=True)

        try:        
            with open(preset_path, 'w') as f:
                f.write(json.dumps(out_list, indent=2))
        except BaseException as e:
            _logger.error(str(e))

    def load_preset(self, preset_path: Path, full=False):
        if self.register_state is not RegisterState.YES:
            _logger.warning(
                f'impossible to load preset, tcp_connected is {self.register_state.name}')
            return
        
        times_dict = dict[str, float]()
        times_dict['start'] = time.time()
        with open(preset_path, 'r') as f:
            in_list = json.load(f)

        times_dict['aft load json'] = time.time()

        for i in range(len(in_list)):
            pg_dict: dict = in_list[i]
            pg_name = pg_dict.get('name', '')
            label = pg_dict.get('label', '')
            n_param = pg_dict.get('n_param', 0)
            is_active = pg_dict.get('is_active', True)
            volume = pg_dict.get('volume', 1.0)
            drywet = pg_dict.get('drywet', 1.0)
            params: dict[int, float] = pg_dict.get('params', {})

            if i >= len(self.plugins):
                _logger.error(
                    'The number of plugins in the preset is superior '
                    'to the current number of carla plugins: '
                    f'({len(in_list)} > {len(self.plugins)})')
                break

            plugin = self.get_plugin(i)
            
            if label != plugin.label:
                _logger.error(
                    f'json import, non matching plugin {i}:\n'
                    f'  {label} != {plugin.label}')
                continue

            if n_param > plugin.n_param:
                _logger.error(
                    f'more params saved than in current plugin {i}\n'
                    f'  {n_param} > {plugin.n_param}')
                continue
            
            if pg_name != plugin.name:
                _logger.warning(
                    f'plugin name in JSON is not the same than in current plugin'
                    f', it may have been renamed:'
                    f'  {pg_name} -> {plugin.name}')
                # not strong error, pass anyway
            
            prepath = f'{self.PREPATH}/{i}'

            if is_active is not plugin.is_active:
                self.carla_send(f'{prepath}/set_active', int(is_active))
            
            if volume != plugin.volume:
                self.carla_send(f'{prepath}/set_volume', volume)
                
            if drywet != plugin.drywet:
                self.carla_send(f'{prepath}/set_volume', drywet)

            if full:
                for param_id_str, attrib_dict in params.items():
                    try:
                        param_id = int(param_id_str)
                        value = float(attrib_dict.get('value'))
                    except:
                        _logger.warning(
                            f'error parsing carla preset {preset_path}:'
                            f'{param_id_str} or value are not int and float')
                        continue

                    # if plugin.label == 'Delay Architect' and param_id == 0:
                    #     self.carla_send(f'{prepath}/set_parameter_value', 0, 0.0)

                    if value != plugin.params[param_id].value:
                        self.carla_send(f'{prepath}/set_parameter_value',
                                        param_id, value)
                        plugin.params[param_id].value = value
            else:
                self.carla_send(f'{prepath}/reset_parameters')
            
                for param_id, attrib_dict in params.items():
                    value = attrib_dict.get('value')
                    if isinstance(value, float):
                        self.carla_send(f'{prepath}/set_parameter_value',
                                        int(param_id), value)

        times_dict['final'] = time.time()
        for key, value in times_dict.items():
            print('timmme', value, key)

    def get_plugin(self, plugin_id: int) -> Plugin:
        if plugin_id >= len(self.plugins):
            plugin = Plugin()
            self.plugins.append(plugin)
            return plugin
        
        return self.plugins[plugin_id]

    def off_ramps(self, on: bool):
        for i in (3, 4):
            self.carla_send(
                f'{self.PREPATH}/{i}/set_parameter_value',
                0, 1.0 if on else 0.0)

    @liblo.make_method('/ctrl/info', 'iiiihiisssssss')
    def _plugin_info(self, path, args):
        self._set_tcp_connected_state(RegisterState.YES)
        
        plugin_id, plg_type, category, hints, unique_id, \
            opt_available, opt_enable, name, filename, icon_name, real_name, \
                label, maker, copyright = args

        plugin = self.get_plugin(plugin_id)
        plugin.name = name
        plugin.label = label
        
    @liblo.make_method('/ctrl/ports', 'iiiiiiii')
    def _plugin_ports(self, path, args):
        plugin_id, audio_ins, audio_outs, midi_ins, midi_outs, \
            param_ins, param_outs, n_param = args
        
        plugin = self.get_plugin(plugin_id)
        plugin.n_param = n_param
    
    @liblo.make_method('/ctrl/paramInfo', 'iissss')
    def _param_info(self, path, args):
        plugin_id, param_id, name, unit, comment, group_name = args
        
        plugin = self.get_plugin(plugin_id)
        param = plugin.params.get(param_id, Param())
        param.name = name
        plugin.params[param_id] = param
    
    @liblo.make_method('/ctrl/paramData', 'iiiiiifff')
    def _param_data(self, path, args):
        plugin_id, param_id, param_type, hints, midi_chn, mapped_ctrl_index, \
            mapped_min, mapped_max, value = args
            
        plugin = self.get_plugin(plugin_id)
        param = plugin.params.get(param_id, Param())
        param.value = value
        param.is_output = bool(param_type == 2)
        
        plugin.params[param_id] = param
    
    @liblo.make_method('/ctrl/paramRanges', 'iiffffff')
    def _param_ranges(self, path, args):
        plugin_id, param_id, default, mini, maxi, \
            step, step_small, step_large = args
        
        plugin = self.get_plugin(plugin_id)
        param = plugin.params.get(param_id, Param())
        param.default = default
        
        plugin.params[param_id] = param

    @liblo.make_method('/ctrl/iparams', 'ifffffff')
    def _internal_param(self, path, args):
        plugin_id, active, drywet, volume, \
            balance_left, balance_right, panning, ctrl_channel = args
        plugin = self.get_plugin(plugin_id)
        plugin.is_active = bool(active >= 0.5)
        plugin.volume = volume
        plugin.drywet = drywet

    @liblo.make_method('/ctrl/cb', 'iiiiifs')
    def _callback(self, path, args):
        action = args[0]
        
        if action >= EngineCallback.PATCHBAY_CLIENT_ADDED:
            return
        
        plugin_id, value1, value2, value3, valuef, value_str = args[1:]
        if action == EngineCallback.PARAMETER_VALUE_CHANGED:
            param_id = value1
            plugin = self.get_plugin(plugin_id)

            if param_id >= 0:
                # plugin.params[param_id].value = valuef
                # plugin.params.get(param_id, default=Param()).value = valuef
                param = plugin.params.get(param_id)
                if param is None:
                    param = Param()
                    plugin.params[param_id] = param
                    _logger.warning(
                        f"creation of param n°{param_id} on plugin {plugin_id}"
                        " via callback /cb PARAMETER_VALUE_CHANGED")
                param.value = valuef
                    
            elif param_id == -2:
                plugin.is_active = bool(valuef > 0.5)
            elif param_id == -3:
                plugin.drywet = valuef
            elif param_id == -4:
                plugin.volume = valuef
        
        if action == EngineCallback.PLUGIN_ADDED:
            plugin = self.get_plugin(plugin_id)
            plugin.name = value_str
        
        if action == EngineCallback.PLUGIN_REMOVED:
            plugin = self.get_plugin(plugin_id)
            self.plugins.remove(plugin)
            return
        
    @liblo.make_method('/ctrl/resp', 'is')
    def _resp(self, path, args):
        ...
        

class Carla(RModule):
    engine: 'MainEngine'
    PREPATH = '/Carla_Multi_Client_Carla_7'
    
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        self.osc_tcp_server = _OscTcpServer(self)
        self.osc_tcp_server.start()
        self.is_tcp_running = False

    def quit(self):
        self.unregister_tcp()
        self.osc_tcp_server.stop()

    def register_tcp(self):
        self.osc_tcp_server.register()
        self.is_tcp_running = True

    def unregister_tcp(self):
        self.is_tcp_running = False
        self.osc_tcp_server.unregister()

    def set_tcp_connected_state(self, tcp_state: RegisterState):
        self.engine.modules['optional_gui'].set_carla_tcp_state(tcp_state)

    def get_tcp_connected_state(self) -> RegisterState:
        return self.osc_tcp_server.register_state

    def set_tempo(self, bpm: float):
        if not self.is_tcp_running:
            return

        self.osc_tcp_server.set_tempo(bpm)

    def _get_presets_dir(self) -> Path:
        presets_dir = (self.engine.modules['nsm_client'].client_path
                       / 'CarlaPresets')
        presets_dir.mkdir(parents=True, exist_ok=True)
        return presets_dir
    
    def list_presets(self) -> list[str]:
        presets_dir = self._get_presets_dir()
        return [f.rpartition('.')[0] for f in os.listdir(presets_dir)
                if f.endswith('.json')]

    def save_preset(self, preset_name: str):
        presets_dir = self._get_presets_dir()
        self.osc_tcp_server.save_preset(
            presets_dir / f'{preset_name}.json', full=True)

    def load_preset(self, preset_name: str):
        presets_dir = self._get_presets_dir()
        preset_path = presets_dir / f'{preset_name}.json'
        if not preset_path.exists():
            _logger.error(f"Impossible to find carla preset {preset_path}")
            return
        self.osc_tcp_server.load_preset(preset_path, full=True)

    def set_song(self, song: SongParameters):
        if isinstance(song, Orage):
            self.load_preset('orage')
        elif isinstance(song, MourirIdees):
            self.load_preset('mouriridées')

    def route(self, address: str, args: list):        
        ...
    
    def off_ramps(self, on:bool):
        self.osc_tcp_server.off_ramps(on)
    
            
        
