from mentat import Engine

class MainEngine(Engine):
    def __init__(self, name, port, folder, debug=False, tcp_port=None, unix_port=None):
        super().__init__(name, port, folder, debug, tcp_port, unix_port)
        self._playing = False