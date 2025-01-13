from keyboard import read_event, KEY_DOWN

class KeyboardApiFacade:
    def __init__(self):
        pass

    def read_event(self):
        return read_event()
    
    def event_type_is_key_down(self, event_type):
        return event_type == KEY_DOWN