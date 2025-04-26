#!/usr/bin/env python
# surveillance/peripherals.py
"""
Wrapper to run peripheral monitors from the project root.
"""

from surveillance.src.util.detect_os import OperatingSystemInfo
from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events
import threading
import os
import sys
import time
import keyboard
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import project modules


# TODO:
# TODO: Change this absolute gong show into two separate files plus an entrypoint
# TODO: The entrypoint detects, "Linux or windows?"
# TODO: And chooses the entrypoint script for the correct OS. No more conditional imports
# TODO:

def on_hotkey():
    exit_all_monitors()


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


if __name__ == "__main__":
    # Detect operating system
    print("HERE 49ru")
    current_os = OperatingSystemInfo()
    print(current_os, "50ru")
    # Import the appropriate modules based on OS
    if current_os.is_windows:
        from surveillance.src.trackers.peripherals.windows.win_keyboard_detector import win_monitor_keyboard
        from surveillance.src.trackers.peripherals.windows.win_mouse_detector import win_monitor_mouse

        # On Windows, we'll use dummy paths since the actual paths aren't needed
        keyboard_path = os.getenv("WINDOWS_KEYBOARD_PATH", "WINDOWS_KEYBOARD")
        mouse_path = os.getenv("WINDOWS_MOUSE_PATH", "WINDOWS_MOUSE")

        chosen_keyboard_monitor = win_monitor_keyboard
        chosen_mouse_monitor = win_monitor_mouse
    else:
        from surveillance.src.trackers.peripherals.linux.linux_peripheral_detector import linux_monitor_keyboard, linux_monitor_mouse
        print("64ru")
        keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
        mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

        chosen_keyboard_monitor = linux_monitor_keyboard
        chosen_mouse_monitor = linux_monitor_mouse
        print(chosen_keyboard_monitor)
        print(chosen_mouse_monitor, "72ru")
    print(keyboard_path, mouse_path, "73ru")
    if keyboard_path is None or mouse_path is None:
        raise ValueError("Failed to load peripheral paths")

    # Register global exit hotkey
    print("Adding exit hotkeys")
    if current_os.is_windows:
        keyboard.add_hotkey('alt+q', exit_all_monitors)
    else:
        from pynput import keyboard as linux_keyboard
        # Create a listener that triggers on alt+q
        with linux_keyboard.GlobalHotKeys({'<alt>+q': on_hotkey}) as h:
            h.join()  # Keep the listener running

    print("Starting monitors. Press Alt+Q to exit all monitors.")

    # Create threads with shared running flag
    keyboard_thread = threading.Thread(
        target=chosen_keyboard_monitor,
        # Pass a function that returns the running state
        args=(keyboard_path, lambda: running),
        daemon=True,
        name="KeyboardMonitorThread"
    )

    mouse_thread = threading.Thread(
        target=chosen_mouse_monitor,
        # Pass the same function to mouse monitor
        args=(mouse_path, lambda: running),
        daemon=True,
        name="MouseMonitorThread"
    )

    # Start threads
    keyboard_thread.start()
    mouse_thread.start()

    try:
        # Main loop - check running flag periodically
        while running:
            time.sleep(0.1)

        # If we get here, running is False, so clean up
        print("Shutting down all monitors...")
        time.sleep(1)  # Give threads time to clean up

    except KeyboardInterrupt:
        print("Interrupted by user")
        running = False
        time.sleep(1)  # Give threads time to clean up

    print("All monitoring stopped")
    sys.exit(0)
