import tkinter as tk
from queue import Queue, Empty
import threading
import re

from ..util.console_logger import ConsoleLogger


class Overlay:
    # TODO: If it is alt tab window, color it
    def __init__(self):
        self.debug = False
        self.logger = ConsoleLogger()

        # Color mapping for different applications
        self.color_map = {
            'Chrome': '#4285F4',    # Google Blue
            'Firefox': '#FF6B2B',   # Firefox Orange
            'Code': '#007ACC',      # VSCode Blue
            'Terminal': '#32CD32',  # Lime Green
            'Slack': '#4A154B',     # Slack Purple
            'Discord': '#7289DA',   # Discord Blue
            'Spotify': '#1DB954',   # Spotify Green
        }
        self.default_color = 'lime'

        self.update_queue = Queue()

        # Create and start the GUI thread
        if self.debug:
            self.logger.log_yellow("[info] Debug mode is on")
            self.gui_thread = threading.Thread(target=self._run_gui)
            self.gui_thread.daemon = True  # Thread will close when main program exits
            self.gui_thread.start()
        else:
            self.logger.log_yellow("[info] Inactive debug display")

    def change_display_text(self, new_text, display_color=None):
        """Thread-safe method to change display text"""
        self.update_queue.put((new_text, display_color))

    def process_queue(self):
        """Process all pending updates"""
        while not self.update_queue.empty():
            try:
                text, color = self.update_queue.get_nowait()
                # print(f"Processing update: {text}, {color}")  # Debug
                self._update_display(text, color)
            except Empty:
                break

    def _update_display(self, new_text, display_color):
        """Actually update the display (called from main thread)"""
        # f"Starting _update_display with: {new_text}, {display_color}")
        formatted_text = self.format_title(new_text)
        color = display_color if display_color else self.get_color_for_window(
            new_text)

        try:
            self.label.config(text=formatted_text, fg=color)
            self.window.update()
        except Exception as e:
            print(f"Error updating display: {e}")  # Debug

    def get_color_for_window(self, title):
        """Determine text color based on window title"""
        title = title.lower()
        for key, color in self.color_map.items():
            if key.lower() in title:
                return color
        return self.default_color  # Default color

    def format_title(self, title):
        """Format the window title for display"""
        linux_cli_pattern = r'^([^\s@]+@[^\s@:]+):'
        match = re.match(linux_cli_pattern, title)
        if match:
            return match.group(1)

        if "Google Chrome" in title:
            parts = title.split(' - ')
            if len(parts) < 2:
                site = ""
            else:
                site = parts[-2]  # Usually the site name is second-to-last
            # return f"Chrome | {site}"
            return f"{site}"
        elif "Visual Studio Code" in title:
            return "VSCode"
        elif "Terminal" in title:
            return "Terminal"
        elif len(title) > 30:  # Truncate very long titles
            return title[:27] + "..."
        elif "PyCharm" in title:
            return "PyCharm"
        return title

    def _run_gui(self):
        """Run the GUI in its own thread"""
        self.window = tk.Tk()
        self.window.title("Overlay")

        # print("Creating window")  # Debug

        # Make window transparent
        self.window.attributes('-alpha', 0.8)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', 1)

        # Configure window appearance
        self.window.configure(bg='black')
        self.label = tk.Label(
            self.window,
            text="Initializing...",  # Add initial text
            font=('Arial', 24, 'bold'),
            fg=self.default_color,
            bg='black',
            padx=10,
            pady=5
        )
        self.label.pack(expand=True, fill='both')  # Make label fill window

        # Position window
        # self.window.geometry('300x100+10+10')  # Give it an explicit size
        self.window.geometry('300x70+10+10')  # Width x Height + X + Y position

        self.window.deiconify()
        self.window.lift()
        self.window.update()

        # Start queue check
        self._schedule_queue_check()

        # Set initial text
        self.change_display_text("Terminal", self.color_map["Terminal"])

        self.window.mainloop()

    def _schedule_queue_check(self):
        """Check for updates every 100ms"""
        # print("Queue check running")
        self.process_queue()
        self.window.after(100, self._schedule_queue_check)
