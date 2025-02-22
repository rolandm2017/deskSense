import tkinter as tk
import subprocess
import time


class Overlay:
    def __init__(self):
        # Create transparent window
        self.window = tk.Tk()
        self.window.title("Overlay")

        # Make window transparent
        self.window.attributes('-alpha', 0.8)  # Slight transparency
        self.window.overrideredirect(True)     # Remove window decorations
        self.window.attributes('-topmost', 1)   # Always on top

        # Configure window appearance
        self.window.configure(bg='black')
        self.label = tk.Label(
            self.window,
            font=('Arial', 24, 'bold'),  # Large, bold font
            fg='lime',                    # Default color
            bg='black',
            padx=10,
            pady=5
        )
        self.label.pack()

        # Position window in top-left corner
        self.window.geometry('+10+10')  # 10px from left, 10px from top

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

        # Start update loop
        self.update_active_window()

    def get_active_window(self):
        """Fetch the active window title"""
        try:
            output = subprocess.check_output(
                "xdotool getactivewindow getwindowname", shell=True).decode().strip()
            return output if output else "Unknown"
        except Exception:
            return "Unknown"

    def get_color_for_window(self, title):
        """Determine text color based on window title"""
        title = title.lower()
        for key, color in self.color_map.items():
            if key.lower() in title:
                return color
        return 'lime'  # Default color

    def format_title(self, title):
        """Format the window title for display"""
        if "Google Chrome" in title:
            parts = title.split(' - ')
            if len(parts) > 1:
                site = parts[-2]  # Usually the site name is second-to-last
                return f"Chrome | {site}"
        elif "Visual Studio Code" in title:
            return "VSCode"
        elif "Terminal" in title:
            return "Terminal"
        elif len(title) > 30:  # Truncate very long titles
            return title[:27] + "..."
        return title

    def update_active_window(self):
        """Update the displayed window title and color"""
        title = self.get_active_window()
        formatted_title = self.format_title(title)
        color = self.get_color_for_window(title)

        # Update label text and color
        self.label.config(text=formatted_title, fg=color)

        # Update every 100ms (10 times per second)
        self.window.after(100, self.update_active_window)


if __name__ == "__main__":
    overlay = Overlay()
    overlay.window.mainloop()
