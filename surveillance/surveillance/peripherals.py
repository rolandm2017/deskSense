#!/usr/bin/env python
"""
Wrapper to run the linux_peripheral_detector from the project root.
"""

import threading
import os
import sys

from dotenv import load_dotenv

# File is surveillance/peripherals.py

from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events
from surveillance.src.util.detect_os import OperatingSystemInfo

load_dotenv()


def debug_logger_aggregate(agg):
    """Debug logger that just prints the aggregate without making network requests"""
    print(f"DEBUG - Mouse aggregate: {agg}")


def debug_logger_keyboard():
    """Debug logger that just prints keyboard events without making network requests"""
    print("DEBUG - Keyboard event detected")

# 
# NOTE: Some prompts for future debugging ideas, left below
#

# # We define custom functions BEFORE importing the module
# # Then we monkey-patch the module to use our functions


# # Conditionally set the handlers based on debug mode
# DEBUG = False

# if DEBUG:
#     print("Running in DEBUG mode - no network requests will be made")
#     # We'll set these as dummy functions that will be injected into the module
#     POST_KEYBOARD_FUNC = debug_logger_keyboard
#     POST_MOUSE_FUNC = debug_logger_aggregate
# else:
#     # We'd use the real ZMQ functions later
#     POST_KEYBOARD_FUNC = publish_keyboard_event  # Will be set to the real function
#     POST_MOUSE_FUNC = publish_mouse_events     # Will be set to the real function

# # Now we can import the module and patch it

# # Now we can monkey-patch the module before using any of its functions


if __name__ == "__main__":
    current_os = OperatingSystemInfo()

    chosen_mouse_monitor = None
    chosen_keyboard_monitor = None

    if current_os.is_windows:
        import surveillance.src.trackers.peripherals.windows.win_keyboard_detector as win_monitor_keyboard
        import surveillance.src.trackers.peripherals.windows.win_mouse_detector as win_monitor_mouse
        keyboard_path = os.getenv("WINDOWS_KEYBOARD_PATH")
        mouse_path = os.getenv("WINDOWS_MOUSE_PATH")
        chosen_keyboard_monitor = win_monitor_keyboard
        chosen_mouse_monitor = win_monitor_mouse

    else:
        from surveillance.src.trackers.peripherals.linux.linux_peripheral_detector import linux_monitor_keyboard, linux_monitor_mouse
        keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
        mouse_path = os.getenv("UBUNTU_MOUSE_PATH")
        chosen_keyboard_monitor = linux_monitor_keyboard
        chosen_mouse_monitor = linux_monitor_mouse

    if keyboard_path is None or mouse_path is None:
        raise ValueError("Failed to load peripheral paths")

    # Create and start threads with the properly patched functions
    keyboard_thread = threading.Thread(
        target=chosen_keyboard_monitor,
        args=(keyboard_path,),
        daemon=True
    )

    mouse_thread = threading.Thread(
        target=chosen_mouse_monitor,
        args=(mouse_path,),
        daemon=True
    )

    keyboard_thread.start()
    mouse_thread.start()

    try:
        # Keep the main thread alive
        keyboard_thread.join()
        mouse_thread.join()
    except KeyboardInterrupt:
        print("Monitoring stopped")
