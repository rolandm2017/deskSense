
import csv
from datetime import datetime

class KeyboardCsvWriter:
    def __init__(self):
        pass
    
    def _log_event_to_csv(self, current_time):
        self.events.append(current_time)
        date_str = current_time.strftime('%Y-%m-%d')
        file_path = self.data_dir / f'key_logging_{date_str}.csv'

        # Create file with headers if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'timestamp'])
                writer.writeheader()
        
        # Log the event
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'timestamp'])
            writer.writerow({
                'date': date_str,
                'timestamp': current_time
            })


class MouseCsvWriter:
    def __init__(self):
        pass

    def log_movement_to_csv(self, event_type, position):
        """
        Log mouse movement events to CSV.
        
        Args:
            event_type (str): Either 'start' or 'stop'
            position (tuple): (x, y) coordinates of mouse position
        """
        # print("Not intended for use")
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
                writer.writeheader()
        
        # Log the event
        event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'x_position': position[0],
                'y_position': position[1]
            }
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
            writer.writerow(event)

        self.session_data.append(event)

    def generate_movement_report(self, date_str=None):
        """
        Generate a report of mouse movement patterns for a specific date.
        
        Args:
            date_str (str): Date in format 'YYYY-MM-DD'. If None, uses current date.
        
        Returns:
            dict: Report containing movement statistics
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        if not file_path.exists():
            return "No mouse tracking data available for this date."
            
        movement_sessions = []
        start_time = None
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event_type'] == 'start':
                    start_time = datetime.fromisoformat(row['timestamp'])
                elif row['event_type'] == 'stop' and start_time:
                    end_time = datetime.fromisoformat(row['timestamp'])
                    duration = (end_time - start_time).total_seconds()
                    movement_sessions.append(duration)
                    start_time = None
        
        if not movement_sessions:
            return {
                'date': date_str,
                'total_movements': 0,
                'avg_movement_duration': 0,
                'total_movement_time': 0
            }
            
        return {
            'date': date_str,
            'total_movements': len(movement_sessions),
            'avg_movement_duration': round(sum(movement_sessions) / len(movement_sessions), 2),
            'total_movement_time': round(sum(movement_sessions), 2)
        }
    

class ProgramCsvWriter:
    def __init__(self):
        pass

    def save_session(self, session, special=""):
        """Save session data to CSV file."""
        # self.console_logger.log_green("Logging to csv: " + session['window'])
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'{special}productivity_{date_str}.csv'
        
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
