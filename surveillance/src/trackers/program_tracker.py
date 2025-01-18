from pathlib import Path

import time
import threading

from ..console_logger import ConsoleLogger
from ..facade.program_facade import ProgramApiFacadeCore
from ..util.detect_os import OperatingSystemInfo
from ..util.end_program_routine import end_program_readout, pretend_report_event
from ..util.clock import Clock
from ..util.threaded_tracker import ThreadedTracker


# TODO: Report mouse, keyboard, program, chrome tabs, every 15 sec, to the db.
# TODO: report only closed loops of mouse, if unclosed, move to next cycle

# TODO: report programs that aren't in the apps list.

class ProgramTrackerCore:
    def __init__(self, clock, program_api_facade, event_handlers):
        self.clock = clock
        self.program_facade: ProgramApiFacade = program_api_facade
        self.event_handlers = event_handlers

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

    def attach_listener(self):
        for window_change in self.program_facade.listen_for_window_changes():
            newly_detected_window = f"{window_change['process_name']} - {window_change['window_title']}"                
            on_a_different_window = newly_detected_window != self.current_window 
            if self.current_window and on_a_different_window:
                self.apply_handlers(self.package_window_into_db_entry(), 500)
                self.console_logger.log_active_program(newly_detected_window)  # FIXME: Program None - rlm@kingdom: ~/Code/deskSense/surveillance
                self.start_time = self.clock.now()

            # Initialize start time if this is the first window
            if not self.start_time:
                self.start_time = self.clock.now()
            
            self.current_window = newly_detected_window

    def run_tracking_loop(self):
        self.attach_listener()

    # def track_window(self):
    #     """Track window activity and productivity."""
    #     try:
    #         window_info = self.get_active_window_info()
    #         if not window_info:
    #             return
    #         # print(window_info, '122fl')
    #         newly_detected_window = f"{window_info['process_name']} - {window_info['window_title']}"
    #         print(newly_detected_window, self.session_data)
            
    #         # If window has changed, log the previous session
    #         on_a_different_window = newly_detected_window != self.current_window 
    #         if self.current_window and on_a_different_window:
    #             self.apply_handlers(self.package_window_into_db_entry(), 99)
    #             self.console_logger.log_active_program(newly_detected_window)
    #             self.start_time = self.clock.now()

    #         # Initialize start time if this is the first window
    #         if not self.start_time:
    #             self.start_time = self.clock.now()
            
    #         self.current_window = newly_detected_window
            
    #     except Exception as e:
    #         print(e)
    #         print(f"Error tracking window: {e}")

    # # FIXME: convert bytestring -> plain string as soon as it enters the system. don't let it leave the facade
    

    def get_active_window_info(self):
        """Get information about the currently active window."""
        try:
            window_info = self.program_facade.read_current_program_info()
            window_info["timestamp"] = self.clock.now()
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

        
    def package_given_window_for_csv(self, window):
        end_time = self.clock.now()
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

        end_time = self.clock.now()
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

        end_time = self.clock.now()
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
        self.apply_handlers(session, 1)

    def report_missing_program(self, title):
        """For when the program isn't found in the productive apps list"""
        self.console_logger.log_yellow(title)  # temp

    def apply_handlers(self, session: dict, source=0):
        #  {'os': 'Ubuntu', 'pid': 70442, 'process_name': 'pgadmin4', 'window_title': 'Alt-tab window'} 
        # start_time, end_time, duration, window, productive
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                handler(session)  # emit an event
        else:
            self.event_handlers(session)  # is a single func                

    def gather_session(self):
        current = self.session_data
        self.session_data = []  # reset
        return current
    
    def stop(self):
        pass  # might need later 



if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    program_api_facade = ProgramApiFacadeCore(os_type)
        
    # folder = Path("/tmp")


    clock = Clock()
        
    try:

        tracker = ProgramTrackerCore(clock, program_api_facade, [end_program_readout, pretend_report_event])
        thread_handler = ThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
