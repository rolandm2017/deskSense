from enum import Enum


class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"


class ChartEventType(Enum):
    MOUSE = "mouse"
    KEYBOARD = "keyboard"


class SystemStatusType(Enum):
    # Type one: When the program is just started
    PROGRAM_STARTED = "program_started"
    # Type two: when it's a "still on" signal
    CONTINUED_USE = "continued_use"
    # Type three: Shutdown.
    SHUTDOWN = "shutdown"
    # If the row is a shutdown, obviously the
    # next read did not show up to make it a "continued_use"
