import sys
import signal
import logging
import liblo
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot

from ui.raymentat import Ui_Dialog

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

def signal_handler(sig, frame):
    QApplication.quit()
    
main_dict = {
    'songs': list[str](),
    'song_index': 0
}


class MainWin(QDialog):
    fill_songs = pyqtSignal()
    song_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.fill_songs.connect(self._fill_songs)
        self.song_changed.connect(self._song_changed)
        
    @pyqtSlot()
    def _fill_songs(self):
        self.ui.comboBoxCurrentSong.clear()
        for song in main_dict['songs']:
            self.ui.comboBoxCurrentSong.addItem(song)
    
    @pyqtSlot()
    def _song_changed(self):
        self.ui.comboBoxCurrentSong.setCurrentIndex(main_dict['song_index'])
    


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
        super().stop()
        self.sendE('/raymentat/jepars')
    
    @liblo.make_method('/raymentat_gui/songs', None)
    def _get_songs(self, path, args: list[str]):
        main_dict['songs'] = args.copy()
        main_win.fill_songs.emit()
        
    @liblo.make_method('/raymentat_gui/current_song', 'i')
    def _get_current_song(self, path, args: list[str]):
        main_dict['song_index'] = args[0]
        main_win.song_changed.emit()





if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWin()
    
    server = OscServer()
    server.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)
    main_win.exec()
    
    server.stop()
    
    _logger.info('Main win exit')
    
    
        
    