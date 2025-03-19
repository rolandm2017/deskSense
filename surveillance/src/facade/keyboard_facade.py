
from collections import deque

from datetime import datetime


class KeyboardFacadeCore:
    def __init__(self):
        # self.listener = keyboard.Listener(on_press=self._on_press)
        # self.listener.start()
        self.queue = deque()

    # def _on_press(self, key):
    #     self.current_event = key

    def add_event(self, time: datetime):
        """It really does need to be a timestamp, because later, the EventAggregator compares timestamps.`"""
        self.queue.append(time.timestamp())

    # def get_next_event(self):
    #     if self.queue:
    #         return self.queue.popleft()  # O(1) operation
    #     return None

    def read_event(self):
        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None
        # event = self.current_event
        # self.current_event = None
        # return event

    def event_type_is_key_down(self, event):
        # print(event, event is not None, "21vv")
        return event is not None  # If event exists, it was a key press

    # def is_ctrl_c(self, event):
    #     is_a_keycode_instance = isinstance(event, keyboard.KeyCode)
    #     char_is_c = None
    #     also_has_ctrl = None
    #     # must do like this to prevent AttributeError: 'Key' object has no attribute 'char'
    #     # because when Ctrl is pressed, ".char" makes no sense, DNE
    #     if is_a_keycode_instance:
    #         also_has_ctrl = keyboard.Key.ctrl == self.listener.canonical(event)
    #         if also_has_ctrl:
    #             char_is_c = event.char == 'c'
    #             if char_is_c:
    #                 print("#-#-#-#-#-#-#-#-")
    #                 print("Ctrl C detected!")
    #                 print("#-#-#-#-#-#-#-#-")
    #                 return True
    #     return (
    #         is_a_keycode_instance and
    #         char_is_c and
    #         also_has_ctrl
    #     )

    # def trigger_ctrl_c(self):
    #     """Runs to shutdown the server as normal"""
    #     print("os.kill is called")
    #     os.kill(os.getpid(), signal.SIGINT)
