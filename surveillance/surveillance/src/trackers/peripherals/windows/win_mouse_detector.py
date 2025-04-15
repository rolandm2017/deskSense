import threading
import os
import sys
import time
import logging
from datetime import datetime
from pynput import mouse

from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events

from surveillance.src.trackers.peripherals.util.mouse_event_aggregator import MouseEventAggregator
from surveillance.src.trackers.peripherals.util.mouse_event_dispatch import MouseEventDispatch

# Set up logging
logging.basicConfig(
    filename='mouselog.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Debug flag
DEBUG = False


def exit_program():
    """Exit the program cleanly"""
    global running
    print("Exit hotkey pressed. Exiting...")
    running = False

def monitor_mouse():
    """Monitor mouse movements and actions"""
    print("Monitoring mouse")
    
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
    print("Starting mouse logger...")
    listener.start()
    
    try:
        # Main dispatch loop
        while running:
            time.sleep(0.2)  # Check every 200ms - adjust as needed
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Clean up before exiting
        listener.stop()
        listener.join()
        print("Mouse logging stopped.")
        print(f"Log file is located at: {os.path.abspath('mouselog.txt')}")

# Define global running flag at module level
running = True

if __name__ == "__main__":
    print("Starting mouse monitoring...")
    print("Press Ctrl+C to exit")
    
    try:
        # Start the mouse monitoring
        monitor_mouse()
    except Exception as e:
        print(f"Error in mouse monitoring: {e}")
    finally:
        running = False
        print("Mouse monitoring stopped.")