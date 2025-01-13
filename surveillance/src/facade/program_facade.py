import win32gui
import win32process
import psutil

class ProgramApiFacade:

    def __init__(self):
        pass

    def read_current_program_info(self):
        window = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(window)[1]
        process = psutil.Process(pid)
        window_title = win32gui.GetWindowText(window)

        return {"window": window, "pid": pid, "process": process, "window_title": window_title}