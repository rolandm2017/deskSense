#!/usr/bin/env python
"""
Wrapper to run the linux_peripheral_detector from the project root.
"""
# File is surveillance/peripherals.py
from src.trackers.linux.linux_peripheral_detector import monitor_keyboard, monitor_mouse
import src.trackers.linux.linux_peripheral_detector as detector
from src.util.mouse_aggregator import MouseEventAggregator
from src.util.clock import SystemClock
import threading
import os
import sys

from dotenv import load_dotenv

# First load the environment variables
load_dotenv()

# Create debug logger functions


def debug_logger_aggregate(agg):
    """Debug logger that just prints the aggregate without making network requests"""
    print(f"DEBUG - Mouse aggregate: {agg}")


def debug_logger_keyboard():
    """Debug logger that just prints keyboard events without making network requests"""
    print("DEBUG - Keyboard event detected")

# THIS IS THE KEY TRICK:
# We define custom functions BEFORE importing the module
# Then we monkey-patch the module to use our functions


# Conditionally set the handlers based on debug mode
DEBUG = True

if DEBUG:
    print("Running in DEBUG mode - no network requests will be made")
    # We'll set these as dummy functions that will be injected into the module
    POST_KEYBOARD_FUNC = debug_logger_keyboard
    POST_MOUSE_FUNC = debug_logger_aggregate
else:
    print("Running in PRODUCTION mode - events will be sent to server")
    # We'd use the real network functions later
    POST_KEYBOARD_FUNC = None  # Will be set to the real function
    POST_MOUSE_FUNC = None     # Will be set to the real function

# Now we can import the module and patch it

# Now we can monkey-patch the module before using any of its functions

if DEBUG:
    # Override the global handlers with our debug versions
    detector.post_keyboard_event = POST_KEYBOARD_FUNC
    detector.post_mouse_events = POST_MOUSE_FUNC

    # CRITICAL: Replace the global mouse_event_dispatch with a debug version
    detector.mouse_event_dispatch = detector.MouseEventDispatch(
        detector.mouse_aggregator,
        POST_MOUSE_FUNC
    )
else:
    # In production mode, we'd use the real functions, but we don't need
    # to patch anything since they're already set up correctly
    pass

# Now we can safely import the rest

if __name__ == "__main__":
    keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
    mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

    if keyboard_path is None or mouse_path is None:
        raise ValueError("Failed to load peripheral paths")

    # Create and start threads with the properly patched functions
    keyboard_thread = threading.Thread(
        target=monitor_keyboard,
        args=(keyboard_path, POST_KEYBOARD_FUNC),
        daemon=True
    )

    mouse_thread = threading.Thread(
        target=monitor_mouse,
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
