
from enum import IntEnum
from typing import TYPE_CHECKING, Any
import time
import threading
import logging
import json
import liblo
from pathlib import Path

from mentat import Module
from songs import SongParameters, Orage

if TYPE_CHECKING:
    from main_engine import MainEngine

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class Param:
    symbol: str
    name: str
    is_output: bool
    default: float
    value: float


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
    
    
class OscTcpServer(liblo.ServerThread):
    def __init__(self) -> None:
        super().__init__(8755, liblo.TCP)
        self.carla_addr = liblo.Address('127.0.0.1', 19998, liblo.TCP)
        self.PREPATH = '/Carla_Multi_Client_Carla_7'
        self.plugins = list[Plugin]()

    def start(self):
        super().start()
        self.carla_send('/unregister',
                        f'osc.tcp://127.0.0.1:{self.port}/ctrl')
        self.carla_send('/register', f'osc.tcp://127.0.0.1:{self.port}/ctrl')

    def stop(self):
        self.carla_send('/unregister',
                        f'osc.tcp://127.0.0.1:{self.port}/ctrl')
        time.sleep(0.005)
        super().stop()
        time.sleep(0.005)
        self.free()

    def carla_send(self, *args):
        self.send(self.carla_addr, *args)

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

                    if value != plugin.params[param_id].value:
                        self.carla_send(f'{prepath}/set_parameter_value',
                                        param_id, value)
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

    @liblo.make_method('/ctrl/info', 'iiiihiisssssss')
    def _plugin_info(self, path, args):
        plugin_id, plg_type, category, hints, unique_id, \
            opt_available, opt_enable, name, filename, icon_name, real_name, \
                label, maker, copyright = args
        # print('chouupi plugin', plugin_id, label, name, filename)
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
                plugin.params[param_id].value = valuef
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
        

class Carla(Module):
    engine: 'MainEngine'
    PREPATH = '/Carla_Multi_Client_Carla_7'
    
    def __init__(self, name, protocol=None, port=None, parent=None):
        super().__init__(name, protocol, port, parent)
        self.params = dict[SongParameters, dict[str, float]]()
        self._all_paths = set[str]()
        self._writing_snapshot = dict[int, dict[int, float]]()
        self._plugins_count = -1
        self._params_count = dict[int, int]()
        self._plugins = dict[int, Plugin]()
        # self._scanning_thread = threading.Thread(target=self.save_snapshot)
        self._writing_preset_name = 'indéfini'
        
        self.osc_tcp_server = OscTcpServer()
        self.osc_tcp_server.start()

    def set_song(self, song: SongParameters):
        client_path = self.engine.modules['nsm_client'].client_path
        
        if isinstance(song, Orage):
            self.osc_tcp_server.load_preset(client_path / 'rololo.json', full=True)

    def start_snapshot(self, preset_name: str):
        self._writing_preset_name = preset_name
        snap_thread = threading.Thread(target=self.save_snapshot)
        snap_thread.start()

    # def route(self, address: str, args: list):
    #     print('repmmmms', address, args)

    def route(self, address: str, args: list):
        print('aeizff', address, args)
        
        if address != '/reply' or not args:
            return

        path: str = args[0]
        if not isinstance(path, str):
            return
        
        if not path.startswith(self.PREPATH + '/'):
            return
        
        shpath = path.replace(self.PREPATH + '/', '', 1)
        
        if shpath == 'get_plugins_count':
            self._plugins_count = args[1]
            # for pg_index in range(self._plugins_count):
            #     self.send(f'{self.PREPATH}/{pg_index}/get_parameters_count')
            return
        
        numstr, slash, command = shpath.partition('/')
        if not numstr.isdigit():
            return
        
        if len(args) < 2:
            return
        othargs = args[1:]
        
        pg_num = int(numstr)
        
        if command == 'get_attributes':
            if len(othargs) != 3:
                return
            factory_id, name, is_active = othargs
            
            
            plugin = self._plugins.get(pg_num, Plugin())
            plugin.label = factory_id
            plugin.name = name
            plugin.is_active = bool(is_active)
            self._plugins[pg_num] = plugin
            return
        
        # print('commannd', command, pg_num,  othargs)
        if command == 'get_parameters_count':
            self._params_count[pg_num] = args[1]
            
            # for pm_index in range(self._params_count[pg_num]):
            #     self.send(
            #         f'{self.PREPATH}/{pg_num}/get_parameter_value', pm_index)
            #     # time.sleep(0.001)
            return
        
        if command == 'get_parameter_infos':
            # _logger.info(f'get param infos {pg_num}, {len(othargs)}')
            if len(othargs) != 9:
                return
            
            pm_index, is_output, symbol, name, unit, default, mini, maxi, value = othargs
            plugin = self._plugins.get(pg_num, Plugin())
            self._plugins[pg_num] = plugin
            param = plugin.params.get(pm_index, Param())
            param.symbol = symbol
            param.name = name
            param.default = default
            param.value = value
            param.is_output = bool(is_output)
            plugin.params[pm_index] = param
            return
        
    def save_snapshot(self):
        _logger.info('start snapshot')
        self._writing_snapshot.clear()
        self._plugins_count = -1
        self._params_count.clear()

        start_time = time.time()

        self.send(f'{self.PREPATH}/get_plugins_count')
        
        for i in range(100):
            if self._plugins_count >= 0:
                break
            time.sleep(0.001)
        else:
            _logger.error('Pas de réponse de get_plugins_count')
            return
        
        for pg_index in range(self._plugins_count):
            self.send(f'{self.PREPATH}/{pg_index}/get_attributes')
            self.send(f'{self.PREPATH}/{pg_index}/get_parameters_count')
            
        for pg_index in range(self._plugins_count):
            for i in range(100):
                if self._params_count.get(pg_index) is not None:
                    break
                else:
                    time.sleep(0.001)
            else:
                _logger.error('Pas de réponse de get_parameters_count')
                return
        
        has_missing_pm = False
        
        for i in range(30):
            _logger.debug(f'on rentre dans la boucle {i}')
            has_missing_pm = False
            
            for pg_index in range(self._plugins_count):
                plugin = self._plugins.get(pg_index, Plugin())
                self._plugins[pg_index] = plugin
                for pm_index in range(self._params_count[pg_index]):
                    param =  plugin.params.get(pm_index)
                    if param is None:
                        # time.sleep(0.00001)
                        self.send(
                            f'{self.PREPATH}/{pg_index}/get_parameter_infos', pm_index)
                        has_missing_pm = True
            
            if has_missing_pm:
                time.sleep(0.1)
            else:
                break

        end_time = time.time()

        if has_missing_pm:
            _logger.error('encore des paramètres manquants')
        else:
            _logger.info('tout est Ok')

        _logger.info('snapshot Carla fait en %.3f' % (end_time - start_time))

        if not has_missing_pm:
            out_dict = {}
            
            for pg_index, plugin in self._plugins.items():
                params_dict = {}
                pg_dict = {'label': plugin.label,
                           'is_active': plugin.is_active,
                           'params': params_dict}
                
                for pm_index, param in plugin.params.items():
                    if param.default != param.value and not param.is_output:
                        params_dict[pm_index] = {'def': param.default, 'value': param.value}
                out_dict[pg_index] = pg_dict
                
            # print(out_dict)
            client_path = self.engine.modules['nsm_client'].client_path
            client_path.mkdir(exist_ok=True, parents=True)
            preset_path = client_path / f'{self._writing_preset_name}.json'
            
            with open(preset_path, 'w') as f:
                f.write(json.dumps(out_dict))
                
    def load_snapshot(self, preset_name: str):
        preset_file = (self.engine.modules['nsm_client'].client_path
                       / f'{preset_name}.json')   
        
        try:
            with open(preset_file, 'r') as f:
                preset_dict: dict = json.load(f)
        except BaseException as e:
            _logger.error(str(e))
            return
        
        if not isinstance(preset_dict, dict):
            _logger.error(f"{str(preset_file)} is not a json dict")
            return
        
        all_plugins = dict[int, Plugin]()
        
        for pg_index, pg_dict in preset_dict.items():
            if not isinstance(pg_index, int) or not isinstance(pg_dict, dict):
                _logger.error(f"{str(preset_file)} has no valid data")
                return
        
            plugin = Plugin()
            plugin.label = pg_dict.get('label')
            plugin.name = pg_dict.get('name')
            plugin.is_active = pg_dict.get('is_active')
            
            params_dict = pg_dict.get('params')
            if not isinstance(params_dict, dict):
                _logger.error(f"{str(preset_file)} has invalid paramss on plugin {pg_index}")
                return

            plugin.params = dict[int, Param]()

            for pm_num, value in params_dict.items():
                if not isinstance(pm_num, int) or not isinstance(value, float):
                    _logger.error(f"invalid param {pm_num} on plugin {pg_index}")
                    return
                
                param = Param()
                param.value = value
                plugin.params[pm_num] = param
                 
            all_plugins[pg_index] = plugin
            
    def disconnect_tcp(self):
        print('disconnect_tcp')
        time.sleep(0.010)
        self.osc_tcp_server.stop()
        time.sleep(0.010)
            
        
