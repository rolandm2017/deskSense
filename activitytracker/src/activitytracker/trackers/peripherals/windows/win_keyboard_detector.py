import keyboard
import logging
import os
import time
from datetime import datetime

from activitytracker.trackers.message_dispatch import publish_keyboard_event


def win_monitor_keyboard(device_path=None, get_running_state=None):
    """
    Windows keyboard monitoring function.

    Args:
        device_path: Not used on Windows, but kept for API consistency
        get_running_state: Function that returns True if monitoring should continue, False to stop
    """

    # Print welcome message
    print("Starting Windows keyboard logger...")

    def on_key_event(event):
        """Callback function for key press events"""
        # Skip key releases, only process key presses
        if event.event_type == "down":
            # Log to console
            key_name = event.name
            publish_keyboard_event()



    # Register callback for all keys
    keyboard.hook(on_key_event)

    try:
        # Main loop - check external running state if provided
        while get_running_state is None or get_running_state():
            time.sleep(0.1)  # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Clean up
        keyboard.unhook_all()
        print("Keyboard logging stopped.")
