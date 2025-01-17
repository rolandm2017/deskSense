class ConsoleLogger:
    def __init__(self):
        self.active = False  # changed manually

    def log_mouse_move(self, win32_cursor_pos):     
        if self.active:
            if win32_cursor_pos is not None:
                self.log_green(f"mouse move at {win32_cursor_pos[0]}, {win32_cursor_pos[1]}")
            # else:
            #     self.log_green("None passed to 'log mouse move'")

    def log_key_press(self, timestamp):
        if self.active:
            self.log_green("Logged " + str(timestamp))

    def log_key_presses(self, count):
        if self.active:
            self.log_green(f"Recorded {count} key presses in the past 3 sec")

    def log_active_program(self, title):
        if self.active:
            self.log_green(f"Program {title} is active")

    def log_chrome_tab(self, title):
        if self.active:
            print(f"Tab {title} is active")

    def system_message(self, arg):
        self.log_green(arg)
    
    def log_yellow(self, message):
        if self.active:
            print(f"\033[93m{message}\033[0m")

    def log_red(self, message):
        if self.active:
            print(f"\033[91m{message}\033[0m")

    def log_green(self, message):
        if self.active:
            print(f"\033[92m{message}\033[0m")

    def log_blue(self, message):
        if self.active:
            print(f"\033[94m{message}\033[0m")

    def log_yellow_multiple(self, *args):
        if self.active:
            print(f"\033[93m{' '.join(str(arg) for arg in args)}\033[0m")

    def log_red_multiple(self, *args):
        if self.active:
            print(f"\033[91m{' '.join(str(arg) for arg in args)}\033[0m")

    def log_green_multiple(self, *args):
        if self.active:
            print(f"\033[92m{' '.join(str(arg) for arg in args)}\033[0m")

    def log_blue_multiple(self, *args):
        if self.active:
            print(f"\033[94m{' '.join(str(arg) for arg in args)}\033[0m")