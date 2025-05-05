# windows_peripherals.py
"""
Used by run_peripherals.py to load the Windows peripheral tracking.

You can also just run this directly.
"""

import threading
import os
import sys
import time
import keyboard
from dotenv import load_dotenv

from surveillance.src.util.detect_os import OperatingSystemInfo
from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events
# Import the appropriate modules based on OS
from surveillance.src.trackers.peripherals.windows.win_keyboard_detector import win_monitor_keyboard
from surveillance.src.trackers.peripherals.windows.win_mouse_detector import win_monitor_mouse

# Load environment variables first
load_dotenv()


# Global running flag to control all threads
running = True


def exit_all_monitors():
    """Exit function that will be called by keyboard shortcut"""
    global running
    print("Exit key combination pressed. Shutting down all monitors...")
    running = False


# Detect operating system
current_os = OperatingSystemInfo()

# On Windows, we'll use dummy paths since the actual paths aren't needed
keyboard_path = os.getenv("WINDOWS_KEYBOARD_PATH", "WINDOWS_KEYBOARD")
mouse_path = os.getenv("WINDOWS_MOUSE_PATH", "WINDOWS_MOUSE")

if keyboard_path is None or mouse_path is None:
    raise ValueError("Failed to load peripheral paths")

# Register global exit hotkey
keyboard.add_hotkey('alt+q', exit_all_monitors)
print("Starting monitors. Press Alt+Q to exit all monitors.")

# Create threads with shared running flag
keyboard_thread = threading.Thread(
    target=win_monitor_keyboard,
    # Pass a function that returns the running state
    args=(keyboard_path, lambda: running),
    daemon=True,
    name="KeyboardMonitorThread"
)

mouse_thread = threading.Thread(
    target=win_monitor_mouse,
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
