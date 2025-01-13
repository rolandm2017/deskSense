from ..util.detect_os import get_os_info
os_type = get_os_info()
if os_type.startswith("Windows"):
    from win32api import GetCursorPos
if os_type.startswith("Ubuntu") or os_type.startswith("Linux"):
    from Xlib import display

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