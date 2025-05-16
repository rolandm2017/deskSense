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
    ONLINE = "online"
    # Type three: Shutdown.
    SHUTDOWN = "shutdown"
    # If the row is a shutdown, obviously the
    # next read did not show up to make it a "continued_use"
    # Type four: A capture session starting.
    TEST_STARTUP = "test_startup"


class PlayerState(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
