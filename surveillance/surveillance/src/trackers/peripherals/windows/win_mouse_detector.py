import threading
import os
import sys
import time
import logging
from datetime import datetime
from pynput import mouse

from surveillance.src.trackers.message_dispatch import publish_mouse_events
from surveillance.src.trackers.peripherals.util.mouse_event_aggregator import MouseEventAggregator
from surveillance.src.trackers.peripherals.util.mouse_event_dispatch import MouseEventDispatch

# Debug flag
DEBUG = False

def win_monitor_mouse(device_path, get_running_state=None):
    """
    Windows implementation of mouse monitoring, designed to be called from peripherals.py
    
    Args:
        device_path: Path to the device (may not be used in Windows implementation)
        get_running_state: Function that returns True if monitoring should continue, False to stop
    """
    print(f"Monitoring mouse: {device_path}")
    
    # Create shared resources
    mouse_aggregator = MouseEventAggregator()
    mouse_event_dispatch = MouseEventDispatch(mouse_aggregator, publish_mouse_events)
    
    def on_move(x, y):
        # Add to aggregator
        mouse_event_dispatch.add_to_aggregator()
        if DEBUG:
            print(f'Mouse moved to ({x}, {y})')
    
    def on_click(x, y, button, pressed):
        # Add to aggregator for clicks
        mouse_event_dispatch.add_to_aggregator()
        if DEBUG:
            print(f'Mouse {"pressed" if pressed else "released"} at ({x}, {y}) with {button}')
    
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
    print("Starting Windows mouse logger...")
    listener.start()
    
    try:
        # Main monitoring loop
        while get_running_state is None or get_running_state():
            time.sleep(0.2)  # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("Mouse monitoring interrupted by user")
    finally:
        # Clean up before exiting
        listener.stop()
        listener.join()
        print("Mouse logging stopped.")

# For standalone testing only
if __name__ == "__main__":
    print("Starting Windows mouse monitoring...")
    print("Press Ctrl+C to exit")
    
    # Set up basic logging for standalone mode
    logging.basicConfig(
        filename='mouselog.txt',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    
    try:
        # Start the mouse monitoring with a dummy device path
        win_monitor_mouse("DUMMY_PATH")
    except Exception as e:
        print(f"Error in mouse monitoring: {e}")
    finally:
        print("Mouse monitoring stopped.")