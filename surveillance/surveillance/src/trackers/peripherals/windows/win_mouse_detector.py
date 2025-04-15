import threading
import os
import sys
import time
from datetime import datetime
from pynput import mouse

from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events
from surveillance.src.trackers.peripherals.util.mouse_event_aggregator import MouseEventAggregator
from surveillance.src.trackers.peripherals.util.mouse_event_dispatch import MouseEventDispatch

DEBUG = False
# Create shared resources that will be used by both platforms
mouse_aggregator = MouseEventAggregator()
mouse_event_dispatch = MouseEventDispatch(mouse_aggregator)


def windows_monitor_mouse(device_path):
    """
    Windows implementation of mouse monitoring, structured similarly to Linux version
    """

    print(f"Monitoring mouse: {device_path}")
    
    def on_move(x, y):
        # Add to aggregator - similar to Linux implementation
        mouse_event_dispatch.add_to_aggregator()
        if DEBUG:
            print(f'Mouse moved to ({x}, {y})')
    
    def on_click(x, y, button, pressed):
        # Add to aggregator for clicks too
        mouse_event_dispatch.add_to_aggregator()
        if DEBUG:
            print(f'Mouse {"pressed" if pressed else "released"} at ({x}, {y})')
    
    def on_scroll(x, y, dx, dy):
        # Add to aggregator for scrolls
        mouse_event_dispatch.add_to_aggregator()
        if DEBUG:
            print(f'Mouse scrolled at ({x}, {y})')
    

    # Start mouse listener
    listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )
    print("Starting mouse logger...")
    listener.start()
    
    # Keep this thread alive until program exits
    while getattr(__builtins__, 'running', True):
        # Periodically dispatch the mouse events from the aggregator
        mouse_event_dispatch.dispatch()
        time.sleep(0.2)  # Check every 200ms - adjust as needed
    
    # Clean up before exiting
    listener.stop()
    listener.join()
