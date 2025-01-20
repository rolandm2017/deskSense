from enum import Enum


class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"


class ChartEventType(Enum):
    MOUSE = "mouse"
    KEYBOARD = "keyboard"
