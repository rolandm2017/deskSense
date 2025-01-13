from Xlib import display
from win32api import GetCursorPos

class MouseApiFacade:
    def __init__(self):
        pass

    def get_cursor_pos(self):
        pass

class UbuntuMouseApiFacade(MouseApiFacade):
    def __init__(self):
        self.display = display.Display()

    def get_cursor_pos(self):
        data = self.display.screen().root.query_pointer()
        return (data.root_x, data.root_y)

class WindowsMouseApiFacade(MouseApiFacade):
    def __init__(self):
        pass

    def get_cursor_pos(self):
        return GetCursorPos()