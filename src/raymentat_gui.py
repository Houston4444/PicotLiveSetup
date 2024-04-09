
import sys
import signal
import logging
import liblo
import subprocess
from PyQt5.QtWidgets import QApplication, QDialog, QCompleter
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot, QSettings

from ui.raymentat import Ui_Dialog

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

def signal_handler(sig, frame):
    QApplication.quit()
    
main_dict = {
    'songs': list[str](),
    'song_index': 0,
    'big_sequence_index': 0,
    'all_vfs5_controls': list[str](),
    'vfs5_controls': 'SEQUENCE',
    'carla_tcp_state': 'NO',
    'carla_presets': list[str](),
    'tempo': 120.00,
    'last_kick_velo': 100
}


class MainWin(QDialog):
    toutestpret = pyqtSignal()
    fill_songs = pyqtSignal()
    song_changed = pyqtSignal()
    big_sequence_changed = pyqtSignal()
    fill_vfs5_controls = pyqtSignal()
    vfs5_controls_changed = pyqtSignal()
    carla_tcp_state = pyqtSignal()
    carla_presets_changed = pyqtSignal()
    tempo_changed = pyqtSignal()
    last_kick_velo_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.fill_songs.connect(self._fill_songs)
        self.song_changed.connect(self._song_changed)
        self.big_sequence_changed.connect(self._big_sequence_changed)
        self.fill_vfs5_controls.connect(self._fill_vfs5_controls)
        self.vfs5_controls_changed.connect(self._vfs5_controls_changed)
        self.carla_tcp_state.connect(self._carla_tcp_state)
        self.carla_presets_changed.connect(self._carla_presets_changed)
        self.tempo_changed.connect(self._tempo_changed)
        self.last_kick_velo_changed.connect(self._last_kick_velo_changed)
        self.toutestpret.connect(self._connect_widgets)
    
    # connected to OSC messages
    
    @pyqtSlot()
    def _connect_widgets(self):
        self.ui.comboBoxCurrentSong.currentIndexChanged.connect(
            self._songbox_index_changed)
        self.ui.spinBox.valueChanged.connect(
            self._spin_big_sequence_changed)
        self.ui.comboBoxArduinoMode.currentTextChanged.connect(
            self._arduinobox_text_changed)
        self.ui.lineEdit.textChanged.connect(self._carla_preset_line_edited)
        self.ui.toolButton.clicked.connect(self._save_preset_clicked)
    
    @pyqtSlot()
    def _fill_songs(self):
        self.ui.comboBoxCurrentSong.clear()
        for song in main_dict['songs']:
            self.ui.comboBoxCurrentSong.addItem(song)
    
    @pyqtSlot()
    def _song_changed(self):
        self.ui.comboBoxCurrentSong.setCurrentIndex(main_dict['song_index'])
        
    @pyqtSlot()
    def _big_sequence_changed(self):
        self.ui.spinBox.setValue(main_dict['big_sequence_index'])
    
    @pyqtSlot()
    def _fill_vfs5_controls(self):
        self.ui.comboBoxArduinoMode.clear()
        for vfs5_controls in main_dict['all_vfs5_controls']:
            self.ui.comboBoxArduinoMode.addItem(vfs5_controls)
    
    @pyqtSlot()
    def _vfs5_controls_changed(self):
        self.ui.comboBoxArduinoMode.setCurrentText(main_dict['vfs5_controls'])
    
    @pyqtSlot()
    def _tempo_changed(self):
        self.ui.labelCurrentTempo.setText('%.2f' % main_dict['tempo'])
    
    @pyqtSlot()
    def _carla_presets_changed(self):
        self.ui.lineEdit.setCompleter(QCompleter(main_dict['carla_presets']))
    
    @pyqtSlot()
    def _carla_tcp_state(self):
        self.ui.labelCarlaTcpState.setText(main_dict['carla_tcp_state'])
        self.ui.toolButton.setEnabled(bool(
            main_dict['carla_tcp_state'] == 'YES' and self.ui.lineEdit.text()))
    
    @pyqtSlot()
    def _last_kick_velo_changed(self):
        self.ui.verticalSlider.setValue(main_dict['last_kick_velo'])
    
    # connected to widgets
    
    @pyqtSlot(int)
    def _songbox_index_changed(self, new_index: int):
        if new_index == main_dict['song_index']:
            return
        server.sendE('/raymentat/change_song', new_index)
    
    @pyqtSlot(int)
    def _spin_big_sequence_changed(self, new_big_sequence: int):
        if new_big_sequence == main_dict['big_sequence_index']:
            return
        server.sendE('/raymentat/change_big_sequence', new_big_sequence)

    @pyqtSlot(str)
    def _arduinobox_text_changed(self, new_text: str):        
        if new_text == main_dict['vfs5_controls']:
            return
        server.sendE('/raymentat/change_vfs5_controls', new_text)
    
    @pyqtSlot(str)
    def _carla_preset_line_edited(self, text: str):
        self.ui.toolButton.setEnabled(bool(
            main_dict['carla_tcp_state'] == 'YES' and self.ui.lineEdit.text()))
    
    @pyqtSlot()
    def _save_preset_clicked(self):
        server.sendE('/raymentat/save_carla_preset', self.ui.lineEdit.text())


class OscServer(liblo.ServerThread):
    def __init__(self):
        super().__init__(4324)
        self._engine_addr = liblo.Address(4687)
    
    def sendE(self, *args):
        self.send(self._engine_addr, *args)
    
    def start(self):
        super().start()
        self.sendE('/raymentat/jarrive')
        
    def stop(self):
        self.sendE('/raymentat/jepars')
        super().stop()
    
    @liblo.make_method('/raymentat_gui/last_kick_velo', 'i')
    def _get_last_kick_velo(self, path, args: list[int]):
        main_dict['last_kick_velo'] = args[0]
        main_win.last_kick_velo_changed.emit()
    
    @liblo.make_method('/raymentat_gui/songs', None)
    def _get_songs(self, path, args: list[str]):
        main_dict['songs'] = args.copy()
        main_win.fill_songs.emit()
    
    @liblo.make_method('/raymentat_gui/current_song', 'i')
    def _get_current_song(self, path, args: list[int]):
        main_dict['song_index'] = args[0]
        main_win.song_changed.emit()
        
    @liblo.make_method('/raymentat_gui/current_big_sequence', 'i')
    def _get_current_big_sequence(self, path, args: list[int]):
        main_dict['big_sequence_index'] = args[0]
        main_win.big_sequence_changed.emit()
    
    @liblo.make_method('/raymentat_gui/all_vfs5_controls', None)
    def _get_vfs5_controls(self, path, args: list[str]):
        main_dict['all_vfs5_controls'] = args.copy()
        main_win.fill_vfs5_controls.emit()
    
    @liblo.make_method('/raymentat_gui/current_vfs5_control', 's')
    def _get_current_vfs5_control(self, path, args: list[str]):
        main_dict['vfs5_controls'] = args[0]
        main_win.vfs5_controls_changed.emit()
    
    @liblo.make_method('/raymentat_gui/carla_presets', None)
    def _get_carla_presets(self, path, args: list[str]):
        main_dict['carla_presets'] = args.copy()
        main_win.carla_presets_changed.emit()

    @liblo.make_method('/raymentat_gui/carla_tcp_state', 's')
    def _get_carla_tcp_state(self, path, args: list[int]):
        main_dict['carla_tcp_state'] = args[0]
        main_win.carla_tcp_state.emit()

    @liblo.make_method('/raymentat_gui/tempo', 'f')
    def _get_tempo(self, path, args: list[float]):
        main_dict['tempo'] = args[0]
        main_win.tempo_changed.emit()
    
    @liblo.make_method('/raymentat_gui/toutestpret', '')
    def _toutestpret(self, path, args):
        main_win.toutestpret.emit()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setOrganizationName('RayMentatPicot')
    settings = QSettings()

    main_win = MainWin()
    geom = settings.value('MainWindow/geometry')
    if geom:
        main_win.restoreGeometry(geom)
    
    server = OscServer()
    server.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)
    main_win.exec()
    
    server.stop()
    
    settings.setValue('MainWindow/geometry', main_win.saveGeometry())
    _logger.info('Main win exit')
    
    
        
    