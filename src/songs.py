

class MultipParameters:
    double_kick_allowed = 100
    mute = False
    velocity_1 = 127


class SongParameters:
    # le seq192 de base
    seq_page = 0
    stop_time = 2.500 # en secondes
    average_tempo = 92.0
    taps_for_tempo = 1
    kick_restarts_cycle = False
    restart_precision: 1.0 # en beats
    restart_acceptability = 0.4 # from 0.0 to 1.0
    tempo_animation_unit = 0.5 # en beats
    tempo_animation_len = 6
    tempo_factor = 0.5
    moving_tempo = 0.00 # en pourcents
    immediate_sequence_switch = False
    tempo_style = ''
    
    # le seq192 impact
    impact_col = 0
    
    # le Multip
    double_kick_allowed = 100 # en ms
    
    mul: MultipParameters
    
    def __init__(self):
        self.mul = MultipParameters()


class Radeaux(SongParameters):
    average_tempo = 92.00
    seq_page = 0


class Avale(SongParameters):
    average_tempo = 99.00
    seq_page = 6


class Euclyde7(SongParameters):
    average_tempo = 140
    seq_page = 9


SONGS = [Radeaux(),
         Avale(),
         Euclyde7()]