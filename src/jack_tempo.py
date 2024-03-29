import jacklib
from jacklib import JackOptions
from mentat import Module

class JackTempoSetter(Module):
    def __init__(self, name: str):
        super().__init__(name)
        self.jack_client = jacklib.client_open(
            'tempo_setter',
            JackOptions.NO_START_SERVER | JackOptions.SESSION_ID,
            None)
        jacklib.set_timebase_callback(self.jack_client, 0, self.timebase_callback, None)

    def close(self):
        jacklib.client_close(self.jack_client)
    
    def timebase_callback(self, a, b, c, d, e):
        return
    
    def set_tempo(self, tempo: float):
        pos = jacklib.jack_position_t()
        pos.valid = 0
        pos.beats_per_minute = tempo
        jacklib.transport_reposition(self.jack_client, pos)
        # jacklib.

        # state = jacklib.transport_query(self.jack_client, jacklib.pointer(pos))
        # jacklib.transport_reposition(self.jack_client, pos)
        # transport_position = TransportPosition(
        #     int(pos.frame),
        #     bool(state),
        #     bool(pos.valid & JackPositionBits.POSITION_BBT),
        #     int(pos.bar),
        #     int(pos.beat),
        #     int(pos.tick),
        #     float(pos.beats_per_minute))