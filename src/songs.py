



class SongParameters:
    # le seq192 de base
    ardour_scene = 0
    seq_page = 0
    stop_time = 2.500 # en secondes
    average_tempo = 92.0
    taps_for_tempo = 1
    tempo_style = ''

    kick_restarts_cycle = False
    restart_precision: 1.0 # en beats
    restart_acceptability = 0.4 # from 0.0 to 1.0
    tempo_animation_unit = 0.5 # en beats
    tempo_animation_len = 6
    tempo_factor = 0.5
    moving_tempo = 0.00 # en pourcents

    immediate_sequence_switch = False
    
    # le seq192 impact
    impact_col = 0
    
    kick_spacing = 100 # en ms
    kick_spacing_beats = 1/4
    open_time_beats = 1/4
    kick_snare_demute = True

    def __repr__(self) -> str:
        return self.__class__.__name__


class Radeaux(SongParameters):
    average_tempo = 92.00
    seq_page = 0


class Avale(SongParameters):
    ardour_scene = 1
    average_tempo = 99.00
    seq_page = 6
    kick_spacing = 50


class Euclyde7(SongParameters):
    average_tempo = 140
    seq_page = 9
    kick_snare_demute = False


class MourirIdees(SongParameters):
    average_tempo = 112
    seq_page = 12

class TestiSpace(SongParameters):
    average_tempo = 90
    seq_page = 7
    
class Orage(SongParameters):
    average_tempo = 140
    seq_page = 10

SONGS = [Radeaux(),
         Avale(),
         Orage(),
         MourirIdees()]