import win32gui
import win32process
import psutil
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
import csv

from .mouse_tracker import MouseTracker
from .keyboard_tracker import KeyboardTracker
# from .keyboard_tracker import KeyActivityTracker


class ProductivityTracker:
    def __init__(self):
        # Define productive applications
        self.productive_apps = {
            'code.exe': 'VSCode',
            'discord.exe': 'Discord',
            'chrome.exe': 'Chrome',
            'windowsterminal.exe': 'Terminal',
            'postman.exe': 'Postman',
            'explorer.exe': 'File Explorer'
        }
        
        # Configuration for what's considered productive
        self.productive_categories = {
            'VSCode': True,
            'Terminal': True,
            'Postman': True,
            'Chrome': None,  # Will be determined by window title
            'Discord': None,  # Will be determined by window title
            'File Explorer': True
        }

        # Productive website patterns (for Chrome)
        self.productive_sites = [
            'github.com',
            'stackoverflow.com',
            'docs.',
            'jira.',
            'confluence.',
            'claude.ai',
            'chatgpt.com'
        ]

        # Initialize tracking data
        self.current_window = None
        self.start_time = None
        self.session_data = []
        
        # Get the project root (parent of src directory)
        current_file = Path(__file__)  # This gets us surveillance/src/productivity_tracker.py
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/
        
        # Create data directory if it doesn't exist
        self.data_dir = project_root / 'productivity_data'
        self.data_dir.mkdir(exist_ok=True)

        self.mouse_tracker = MouseTracker(self.data_dir)
        self.keyboard_tracker = KeyboardTracker(self.data_dir)
        # self.key_tracker = KeyActivityTracker(self.data_dir)
        # self.key_tracker.start()


    def get_active_window_info(self):
        """Get information about the currently active window."""
        try:
            window = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            window_title = win32gui.GetWindowText(window)
            
            return {
                'title': window_title,
                'process_name': process.name().lower(),
                'pid': pid,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None

    def is_productive(self, window_info):
        """Determine if the current window represents productive time."""
        if not window_info:
            return False

        process_name = window_info['process_name']
        window_title = window_info['title']

        # Check if it's a known application
        if process_name in self.productive_apps:
            app_name = self.productive_apps[process_name]
            productivity = self.productive_categories[app_name]
            print("process name in productive apps")
            print("productivity", productivity, app_name)
            # If productivity is None, we need to check the window title
            if productivity is None:
                # For Chrome, check if the title contains any productive sites
                if app_name == 'Chrome':
                    print("near any")
                    print(window_title, "::", self.productive_sites)
                    return any(site in window_title.lower() for site in self.productive_sites)
                # For Discord, consider it productive only if specific channels/servers are active
                elif app_name == 'Discord':
                    productive_channels = ['work-', 'team-', 'project-']
                    return any(channel in window_title.lower() for channel in productive_channels)
            
            return productivity

        return False

    def track_window(self, interval=1):
        """Track window activity and productivity."""
        try:
            window_info = self.get_active_window_info()
            if not window_info:
                return

            current_window = f"{window_info['process_name']} - {window_info['title']}"
            
            # If window has changed, log the previous session
            if self.current_window and current_window != self.current_window:
                self.log_session()
                self.start_time = datetime.now()
            
            # Initialize start time if this is the first window
            if not self.start_time:
                self.start_time = datetime.now()
            
            self.current_window = current_window
            
        except Exception as e:
            print(f"Error tracking window: {e}")

    def log_session(self):
        """Log the current session data."""
        if not self.current_window or not self.start_time:
            return

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        window_info = self.get_active_window_info()
        is_productive = self.is_productive(window_info) if window_info else False
        
        session = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'window': self.current_window,
            'productive': is_productive
        }
        
        self.session_data.append(session)
        self.save_session(session)

    def save_session(self, session):
        """Save session data to CSV file."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'productivity_{date_str}.csv'
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['start_time', 'end_time', 'duration', 'window', 'productive'])
                writer.writeheader()
        
        # Append session data
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['start_time', 'end_time', 'duration', 'window', 'productive'])
            writer.writerow(session)

    def generate_report(self, date_str=None):
        """Generate a productivity report for a specific date."""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        file_path = self.data_dir / f'productivity_{date_str}.csv'
        if not file_path.exists():
            return "No data available for this date."
        
        productive_time = 0
        unproductive_time = 0
        app_times = {}
        chrome_sites = {}
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                duration = float(row['duration'])
                window = row['window']
                
                # Track productive/unproductive time
                if row['productive'].lower() == 'true':
                    productive_time += duration
                else:
                    unproductive_time += duration
                
                # Parse application and site data
                parts = window.split(' - ', 1)
                app = parts[0].lower()
                
                # Convert duration to hours
                duration_hours = duration / 3600
                
                # Handle Chrome sites separately
                if app == 'chrome.exe' and len(parts) > 1:
                    title = parts[1].lower()
                    # Extract domain from title (simple version)
                    for site in self.productive_sites:
                        if site in title:
                            chrome_sites[site] = chrome_sites.get(site, 0) + duration_hours
                    # If not a productive site, group under "other"
                    if not any(site in title for site in self.productive_sites):
                        chrome_sites["other"] = chrome_sites.get("other", 0) + duration_hours
                
                # Group by application
                app_name = self.productive_apps.get(app, app)
                app_times[app_name] = app_times.get(app_name, 0) + duration_hours
        
        total_time = productive_time + unproductive_time
        productive_percentage = (productive_time / total_time * 100) if total_time > 0 else 0
        
        # Round all times to 2 decimal places
        app_times = {k: round(v, 2) for k, v in app_times.items()}
        chrome_sites = {k: round(v, 2) for k, v in chrome_sites.items()}
        
        # If Chrome exists in app_times and we have site data, nest it
        if 'Chrome' in app_times and chrome_sites:
            app_times['Chrome'] = {'total': app_times['Chrome'], 'sites': chrome_sites}
        
        return {
            'date': date_str,
            'productive_time': round(productive_time / 3600, 2),
            'unproductive_time': round(unproductive_time / 3600, 2),
            'productive_percentage': round(productive_percentage, 1),
            'app_times': app_times
        }
    
    def cleanup(self):  # Add this method to ProductivityTracker
        """Clean up resources before exit."""
        self.mouse_tracker.stop()
        self.keyboard_tracker.stop()