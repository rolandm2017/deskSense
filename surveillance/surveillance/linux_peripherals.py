# linux_peripherals.py
"""
Used by run_peripherals.py to load the Linux peripheral tracking.

You can also just run this directly.
"""
import threading
import os
import sys
import time
from pynput import keyboard as pynput_keyboard
from dotenv import load_dotenv

from surveillance.src.trackers.peripherals.linux.linux_peripheral_detector import linux_monitor_keyboard, linux_monitor_mouse

from surveillance.src.util.detect_os import OperatingSystemInfo
from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events

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

# Import the appropriate modules based on OS

keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

if keyboard_path is None or mouse_path is None:
    raise ValueError("Failed to load peripheral paths")


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
# Register global exit hotkey
on_alt_q_press.alt_pressed = False

# Start the keyboard listener
keyboard_listener = pynput_keyboard.Listener(
    on_press=on_alt_q_press,
    on_release=on_key_release
)

print("Starting monitors. Press Alt+Q to exit all monitors.")

# Create threads with shared running flag
keyboard_thread = threading.Thread(
    target=linux_monitor_keyboard,
    # Pass a function that returns the running state
    args=(keyboard_path),
    # args=(keyboard_path, lambda: running),
    daemon=True,
    name="KeyboardMonitorThread"
)

mouse_thread = threading.Thread(
    target=linux_monitor_mouse,
    # Pass the same function to mouse monitor
    args=(mouse_path),
    # args=(mouse_path, lambda: running),
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
