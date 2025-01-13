from win32api import GetCursorPos

class MouseApiFacade:
    def __init__(self):
        pass

    def get_cursor_pos(self):
        return GetCursorPos()