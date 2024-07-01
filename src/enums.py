from enum import IntFlag

class FsButton(IntFlag):
    NONE = 0x00
    FS_B = 0x01
    FS_1 = 0x02
    FS_2 = 0x04
    FS_3 = 0x08
    FS_4 = 0x10