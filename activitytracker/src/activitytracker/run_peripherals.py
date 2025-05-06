#!/usr/bin/env python
# activitytracker/peripherals.py
"""
Wrapper to run peripheral monitors from the project root.
"""

from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events
import threading
import os
import sys
import time
from pynput import keyboard as pynput_keyboard

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import project modules


def debug_logger_aggregate(agg):
    """Debug logger that just prints the aggregate without making network requests"""
    print(f"DEBUG - Mouse aggregate: {agg}")


def debug_logger_keyboard():
    """Debug logger that just prints keyboard events without making network requests"""
    print("DEBUG - Keyboard event detected")


# Global running flag to control all threads
running = True


def exit_all_monitors():
    """Exit function that will be called by keyboard shortcut"""
    global running
    print("Exit key combination pressed. Shutting down all monitors...")
    running = False


# Create a keyboard listener with pynput
def on_alt_q_press(key):
    # Check if Alt+Q is pressed
    try:
        if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
            # Set a flag that Alt is pressed
            on_alt_q_press.alt_pressed = True
        elif on_alt_q_press.alt_pressed and hasattr(key, 'char') and key.char == 'q':
            exit_all_monitors()
    except AttributeError:
        pass

# Reset the alt_pressed flag on key release


def on_key_release(key):
    if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
        on_alt_q_press.alt_pressed = False


# Initialize the flag
on_alt_q_press.alt_pressed = False


if __name__ == "__main__":
    # Detect operating system
    current_os = OperatingSystemInfo()

    # Setup of threads handled in OS specific scripts
    # Starting trackers handled in OS specific scripts
    # Import the appropriate modules based on OS
    if current_os.is_windows:
        from activitytracker.windows_peripherals import run_windows_monitors
        run_windows_monitors()
    else:
        from activitytracker.linux_peripherals import run_linux_monitors
        run_linux_monitors()
    try:
        # Main loop - check running flag periodically
        while running:
            time.sleep(0.1)

        print("Shutting down all monitors...")
        time.sleep(1)  # Give threads time to clean up

    except KeyboardInterrupt:
        print("Interrupted by user")
        running = False
        time.sleep(1)  # Give threads time to clean up

    print("All monitoring stopped")
    sys.exit(0)
