
from chansons.song_parameters import SongParameters
from chansons.orage import Orage
from chansons.mourir_idees import MourirIdees


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


class TestiSpace(SongParameters):
    average_tempo = 90
    seq_page = 7


SONGS = [Radeaux(),
         Avale(),
         Orage(),
         MourirIdees()]