class ConsoleLogger:
    def __init__(self):
        self.active = False

    def log_mouse_move(self, win32_cursor_pos):
        print(win32_cursor_pos, "6vv")
     
        if self.active:
            print(f"mouse move at {win32_cursor_pos[0]}, {win32_cursor_pos[1]}")

    def log_key_presses(self, count):
        if self.active:
            print(f"Recorded {count} key presses in the past 3 sec")

    def log_active_program(self, title):
        if self.active:
            print(f"Program {title} is active")

    def log_chrome_tab(self, title):
        if self.active:
            print(f"Tab {title} is active")