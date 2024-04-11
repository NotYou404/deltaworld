from enum import StrEnum, IntEnum


class Font(StrEnum):
    """
    Fonts used for the game. Base sizes:
    - november: 12
    """
    november = "November"


class Entrance(IntEnum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3
