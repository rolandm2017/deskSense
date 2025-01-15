from datetime import datetime
from pathlib import Path
import csv
import time

from ..console_logger import ConsoleLogger
from ..facade.program_facade import ProgramApiFacade
from ..util.detect_os import OperatingSystemInfo


# TODO: Report mouse, keyboard, program, chrome tabs, every 15 sec, to the db.
# TODO: report only closed loops of mouse, if unclosed, move to next cycle

# TODO: report programs that aren't in the apps list.

class ProgramTracker:
    def __init__(self, data_dir, program_api_facade, dao):
        self.data_dir = data_dir
        self.program_facade: ProgramApiFacade = program_api_facade
        self.dao = dao
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
        self.session_data = []  # holds sessions
        self.console_logger = ConsoleLogger()
        
        # Get the project root (parent of src directory)
        current_file = Path(__file__)  # This gets us surveillance/src/productivity_tracker.py
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/
        
        # Create data directory if it doesn't exist
        self.data_dir = project_root / 'productivity_logs'
        self.data_dir.mkdir(exist_ok=True)

        # self.key_tracker = KeyActivityTracker(self.data_dir)
        # self.key_tracker.start()


    def get_active_window_info(self):
        """Get information about the currently active window."""
        try:
            window_info = self.program_facade.read_current_program_info()
            window_info["timestamp"] = datetime.now()
            return window_info
            # return {
            #     'title': window_info["window_title"],
            #     'process_name': window_info["process"].name().lower(),
            #     'pid': window_info["pid"],
            #     'timestamp': datetime.now()
            # }
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None

    def is_productive(self, window_info):
        """Determine if the current window represents productive time."""
        if not window_info:
            return False

        process_name = window_info['process_name']
        window_title = window_info['window_title']
        print(process_name, '92fl')

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
            print(window_info, '122fl')
            newly_detected_window = f"{window_info['process_name']} - {window_info['window_title']}"
            
            # If window has changed, log the previous session
            if self.current_window and newly_detected_window != self.current_window:
                # self.log_session()
                self.log_program_to_db()
                self.console_logger.log_active_program(newly_detected_window)
                self.start_time = datetime.now()

            # Initialize start time if this is the first window
            if not self.start_time:
                self.start_time = datetime.now()
            
            self.current_window = newly_detected_window
            
        except Exception as e:
            print(e)
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
        
        self.session_data.append(session)  # is only used to let surveillanceManager gather the session
        self.log_program_to_db(session)
        # self.save_session(session)

    def report_missing_program(self, title):
        """For when the program isn't found in the productive apps list"""
        print(title)  # temp

    def log_program_to_db(self, session):
        # start_time, end_time, duration, window, productive
        self.dao.create(session)

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

    def gather_session(self):
        current = self.session_data
        self.session_data = []  # reset
        return current

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
    
    def stop(self):
        pass  # might need later
    

# TODO: make it work when run as a script

def end_program_readout():
    print("Ending program tracking...")

if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    program_api_facade = ProgramApiFacade(os_type)
        
    folder = Path("/tmp")

    try:
        instance = ProgramTracker(folder, program_api_facade)
        print("Starting program tracking...")
        
        # Main tracking loop
        while True:
            instance.track_window()
            time.sleep(1)
            
    except KeyboardInterrupt:
        instance.stop()
        end_program_readout()
        # Give time for cleanup
        time.sleep(0.5)
