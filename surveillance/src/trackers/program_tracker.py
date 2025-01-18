from datetime import datetime
from pathlib import Path
import asyncio

import csv
import time
import threading
from threading import Thread

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
        self.program_dao = dao
        self.loop = asyncio.get_event_loop()

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
        
        current_file = Path(__file__)  # This gets us surveillance/src/productivity_tracker.py
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/
        
        self.data_dir = project_root / 'productivity_logs'
        self.data_dir.mkdir(exist_ok=True)

    def start(self):  # copied 'start' method over from keyboard_tracker
        self.is_running = True
        self.monitor_thread = Thread(target=self.attach_listener)
        self.monitor_thread.daemon = True  # Thread will exit when main program exits
        self.monitor_thread.start()

    def attach_listener(self):
        for window_change in self.program_facade.listen_for_window_changes():
            # window_is_chrome = self.window_is_chrome(window_change)
            # if window_is_chrome:  # TEMP logging
            #     self.console_logger.log_blue("Writing to csv")
            #     self.save_session(self.package_given_window_for_csv(window_change), "foo_")

            newly_detected_window = f"{window_change['process_name']} - {window_change['window_title']}"
                
            on_a_different_window = newly_detected_window != self.current_window  # doot
            # print(self.current_window, newly_detected_window, on_a_different_window, '++++\n____\n90ru')
            if self.current_window and on_a_different_window:
                # print("HERE 93ru")
                self.log_program_to_db(self.package_window_into_db_entry(), 500)
                self.console_logger.log_active_program(newly_detected_window)  # FIXME: Program None - rlm@kingdom: ~/Code/deskSense/surveillance
                self.start_time = datetime.now()

            # Initialize start time if this is the first window
            if not self.start_time:
                self.start_time = datetime.now()
            
            self.current_window = newly_detected_window

    def get_active_window_info(self):
        """Get information about the currently active window."""
        try:
            window_info = self.program_facade.read_current_program_info()
            window_info["timestamp"] = datetime.now()
            return window_info
        except Exception as e:
            print(f"Error getting window info: {e}")
            raise e
            return None
        
    def window_is_chrome(self, new_window):
        # example: 'Fixing datetime.fromisoformat() error - Claude - Google Chrome'
        window_title = new_window["window_title"]
        return window_title.endswith('Google Chrome')
        

    def is_productive(self, window_info):
        """Determine if the current window represents productive time."""
        if not window_info:
            return False

        process_name = window_info['process_name']
        window_title = window_info['window_title']

        # Check if it's a known application
        if process_name in self.productive_apps:
            app_name = self.productive_apps[process_name]
            productivity = self.productive_categories[app_name]
            # self.console_logger.log_green("process name in productive apps")
            self.console_logger.log_green_multiple("productivity", productivity, app_name)
            # If productivity is None, we need to check the window title
            if productivity is None:
                # For Chrome, check if the title contains any productive sites
                if app_name == 'Chrome':
                    self.console_logger.log_green_multiple(window_title, "::", self.productive_sites)
                    return any(site in window_title.lower() for site in self.productive_sites)
                # For Discord, consider it productive only if specific channels/servers are active
                elif app_name == 'Discord':
                    productive_channels = ['work-', 'team-', 'project-']
                    return any(channel in window_title.lower() for channel in productive_channels)
            
            return productivity

        return False

    def track_window(self, interval=1):
        """Track window activity and productivity."""
        while self.is_running:
            try:
                window_info = self.get_active_window_info()
                if not window_info:
                    return
                # print(window_info, '122fl')
                newly_detected_window = f"{window_info['process_name']} - {window_info['window_title']}"
                print(newly_detected_window, self.session_data)
                
                # If window has changed, log the previous session
                if self.current_window and newly_detected_window != self.current_window:
                    self.log_program_to_db(self.package_window_into_db_entry(), 99)
                    print("168ru")
                    self.console_logger.log_active_program(newly_detected_window)
                    self.start_time = datetime.now()

                # Initialize start time if this is the first window
                if not self.start_time:
                    self.start_time = datetime.now()
                
                self.current_window = newly_detected_window
                
            except Exception as e:
                print(e)
                print(f"Error tracking window: {e}")

    # FIXME: convert bytestring -> plain string as soon as it enters the system. don't let it leave the facade
        
    def package_given_window_for_csv(self, window):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()        
        is_productive = self.is_productive(window)
        print(window, '188ru')
        session = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'window': window["window_title"],
            'productive': is_productive  # doot
        }
        return session

    def package_window_into_db_entry(self):
        if not self.current_window or not self.start_time:
            return

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        window_info = self.get_active_window_info()
        is_productive = self.is_productive(window_info) if window_info else False
        # print("current window:", self.current_window, "81ru")
        session = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'window': self.current_window.split(" - ", maxsplit=1)[1],
            'productive': is_productive  # doot
        }
        return session

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
            'productive': is_productive  # doot
        }
        
        self.session_data.append(session)  # is only used to let surveillanceManager gather the session
        print(session, "is an empty array right, 197ru")
        self.log_program_to_db(session, 1)

    def report_missing_program(self, title):
        """For when the program isn't found in the productive apps list"""
        self.console_logger.log_yellow(title)  # temp

    def log_program_to_db(self, session: dict, source=0):
        #  {'os': 'Ubuntu', 'pid': 70442, 'process_name': 'pgadmin4', 'window_title': 'Alt-tab window'} 
        # start_time, end_time, duration, window, productive
        # print(session, "206ru")
        # self.console_logger.log_blue(session)
        self.loop.create_task(self.program_dao.create(session))

    def gather_session(self):
        current = self.session_data
        self.session_data = []  # reset
        return current

    
    def stop(self):
        pass  # might need later 
    


def end_program_readout():
    ConsoleLogger.system_message("Ending program tracking...")

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
