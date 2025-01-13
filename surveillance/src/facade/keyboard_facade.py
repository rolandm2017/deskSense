# pynput is superior to the keyboard module, because pynput is "truly cross platform"

from pynput import keyboard

class KeyboardApiFacade:
    def __init__(self):
        self.current_event = None
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
    
    def _on_press(self, key):
        self.current_event = key
    
    def read_event(self):
        event = self.current_event
        # FIXME: if read event is called after 4 presses, you get only the final entering. so press => Read, press => Read will work
        print(event, 'in facade 16rm')
        self.current_event = None
        return event
    
    def event_type_is_key_down(self, event):
        print(event, event is not None, "21rm")
        return event is not None  # If event exists, it was a key press