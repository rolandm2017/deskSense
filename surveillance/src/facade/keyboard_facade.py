
from pynput import keyboard
import signal
import os
#
# pynput is superior to the keyboard module, because pynput is "truly cross platform"
#


class KeyboardApiFacadeCore:
    def __init__(self):
        self.current_event = None
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

    def _on_press(self, key):
        self.current_event = key
        if self.is_ctrl_c(key):
            self.trigger_ctrl_c()

    def read_event(self):
        event = self.current_event
        # FIXME: if read event is called after 4 presses, you get only the final entering. so press => Read, press => Read will work
        if isinstance(event, keyboard.KeyCode):
            # Prevent accidentally logging your password!
            # Create new KeyCode with empty char - No keylogging!
            event = keyboard.KeyCode(char='')
        self.current_event = None
        return event

    def event_type_is_key_down(self, event):
        # print(event, event is not None, "21vv")
        return event is not None  # If event exists, it was a key press

    def is_ctrl_c(self, event):
        is_a_keycode_instance = isinstance(event, keyboard.KeyCode)
        char_is_c = None
        also_has_ctrl = None
        # must do like this to prevent AttributeError: 'Key' object has no attribute 'char'
        # because when Ctrl is pressed, ".char" makes no sense, DNE
        if is_a_keycode_instance:
            also_has_ctrl = keyboard.Key.ctrl == self.listener.canonical(event)
            if also_has_ctrl:
                char_is_c = event.char == 'c'
                if char_is_c:
                    print("#-#-#-#-#-#-#-#-")
                    print("Ctrl C detected!")
                    print("#-#-#-#-#-#-#-#-")
                    return True
        return (
            is_a_keycode_instance and
            char_is_c and
            also_has_ctrl
        )

    def trigger_ctrl_c(self):
        """Runs to shutdown the server as normal"""
        print("os.kill is called")
        os.kill(os.getpid(), signal.SIGINT)
