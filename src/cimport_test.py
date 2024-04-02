from pathlib import Path
from ctypes import cdll, CDLL, RTLD_GLOBAL

this_path = Path(__file__)
print('this path', this_path)

jacklib = cdll.LoadLibrary('libjack.so.0')
so_file = CDLL(str(this_path.parent / 'timebase_master.so'), mode = RTLD_GLOBAL)