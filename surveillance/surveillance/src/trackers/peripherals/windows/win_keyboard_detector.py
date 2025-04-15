# https://claude.ai/chat/43a22b18-4502-489c-aacf-1bcc6f550d55

import keyboard 
import logging
import os
import time
from datetime import datetime

from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events

# Set up logging
logging.basicConfig(
    filename='keylog.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Print welcome message
print("Starting keyboard logger...")
print("Press Alt+Q to exit")

# Flag to control the main loop
running = True

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

def exit_program():
    """Exit the program cleanly"""
    global running
    print("Exit key combination pressed. Exiting...")
    running = False

# Register the exit hotkey
keyboard.add_hotkey('alt+q', exit_program)

# Register callback for all keys
keyboard.hook(on_key_event)

try:
    # Main loop
    while running:
        time.sleep(0.1)  # Sleep to prevent high CPU usage
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    # Clean up
    keyboard.unhook_all()
    print("Keyboard logging stopped.")
    print(f"Log file is located at: {os.path.abspath('keylog.txt')}")