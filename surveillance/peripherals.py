#!/usr/bin/env python
"""
Wrapper to run the linux_peripheral_detector from the project root.
"""
import threading
import sys
import importlib.util
import os

from dotenv import load_dotenv

from src.util.clock import SystemClock
from src.util.mouse_aggregator import MouseEventAggregator
from src.trackers.linux.linux_peripheral_detector import monitor_keyboard, monitor_mouse
from src.trackers.linux.linux_api import post_keyboard_event, post_mouse_events

load_dotenv()

if __name__ == "__main__":
    keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
    mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

    if keyboard_path is None or mouse_path is None:
        raise ValueError("Failed to load peripheral paths")

    # Create and start threads
    keyboard_thread = threading.Thread(
        target=monitor_keyboard, args=(keyboard_path,), daemon=True)
    mouse_thread = threading.Thread(
        target=monitor_mouse, args=(mouse_path,), daemon=True)

    keyboard_thread.start()
    # mouse_thread.start()

    try:
        # Keep the main thread alive
        keyboard_thread.join()
        # mouse_thread.join()
    except KeyboardInterrupt:
        print("Monitoring stopped")
