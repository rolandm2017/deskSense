from pynput import mouse
import time


from ..util.mouse_event_aggregator import MouseEventAggregator
from ..util.mouse_event_dispatch import MouseEventDispatch

from ..message_dispatch import publish_keyboard_event, publish_mouse_events

def on_move(x, y):
    """Callback function that's called when the mouse moves"""
    print(f'Mouse moved to ({x}, {y})')

    
    # You can add your custom logic here:
    # - Track movement patterns
    # - Calculate distance moved
    # - Detect idle time
    # - Trigger other actions

def main():
    print("Mouse movement detector started. Press Ctrl+C to exit.")
    
    # Create a listener that reports mouse movement events
    listener = mouse.Listener(on_move=on_move)
    
    # Start the listener in a non-blocking way
    listener.start()
    
    try:
        # Keep the program running
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("Mouse movement detector stopped.")
    finally:
        # Stop the listener when the program ends
        listener.stop()
        listener.join()
