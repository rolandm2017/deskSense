from enum import Enum


class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"


class ChartEventType(Enum):
    MOUSE = "mouse"
    KEYBOARD = "keyboard"


class SystemStatusType(Enum):
    POWER_ON = "power on"  # When the computer powers on
    SHUTDOWN = "shutdown"  # When the user shuts the computer down (not sleeps)
    CTRL_C_SIGNAL = "ctrl_c_signal"  # Developer presses Ctrl C
    # Tells the db to ignore the next power_on signal, as it's a restart due to code change
    HOT_RELOAD_STARTED = "restart_signal"  # Hot reload
    # Tells the db that this is the server coming back online from a code change
    HOT_RELOAD_CONCLUDED = "restart_recovery"  # Hot reload
    STARTUP = "startup"  # Program comes online
    SLEEP = "sleep"  # User puts the computer to sleep
    WAKE = "wake"  # User wakes the computer from sleep

    # NOTE re: STARTUP: It's impossible for the program to run before the computer does.
