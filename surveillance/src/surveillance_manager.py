# import win32gui
# import win32process
# import psutil
# import time
# from datetime import datetime, timedelta
# import json
from pathlib import Path
# import csv

from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.program_dao import ProgramDao
from .trackers.mouse_tracker import MouseTracker
from .trackers.keyboard_tracker import KeyboardTracker
from .trackers.program_tracker import ProgramTracker
from .facade.keyboard_facade import KeyboardApiFacade
from .facade.mouse_facade import MouseApiFacade, UbuntuMouseApiFacade
from .facade.program_facade import ProgramApiFacade
from .util.interrupt_handler import InterruptHandler
from .util.detect_os import OperatingSystemInfo
# from .keyboard_tracker import KeyActivityTracker


# TODO: Report mouse, keyboard, program, chrome tabs, every 10 sec, to the db.
# TODO: report only closed loops of mouse, if unclosed, move to next cycle


class SurveillanceManager:
    def __init__(self, db_conn, shutdown_signal=None):
        self.db = db_conn
        # Initialize tracking data
        self.current_window = None
        self.start_time = None
        self.session_data = []
        
        # Get the project root (parent of src directory)
        current_file = Path(__file__)  # This gets us surveillance/src/productivity_tracker.py
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/
        
        # Create data directory if it doesn't exist
        self.data_dir = project_root / 'productivity_logs'
        self.data_dir.mkdir(exist_ok=True)

        current_os = OperatingSystemInfo()

        keyboard_facade = KeyboardApiFacade()  # FIXME: one of these 3 is supposed to be initialized in the tracker, with an argument? I think?
        mouse_facade = UbuntuMouseApiFacade()  # TODO: choose the mouseApi facade based on OS
        program_facade = ProgramApiFacade(current_os)
        # interrupt_handler = InterruptHandler

        self.mouse_dao = MouseDao(self.db)
        self.keyboard_dao = KeyboardDao(self.db)
        self.program_dao = ProgramDao(self.db)
        self.chrome_dao = ChromeDao(self.db)

        self.program_tracker = ProgramTracker(self.data_dir, program_facade, self.program_dao)
        self.mouse_tracker = MouseTracker(self.data_dir, mouse_facade, self.mouse_dao)
        self.keyboard_tracker = KeyboardTracker(self.data_dir, keyboard_facade, self.keyboard_dao)
        # self.key_tracker = KeyActivityTracker(self.data_dir)
        self.keyboard_tracker.start()
        self.mouse_tracker.start()
        self.program_tracker.start()
    

    def gather_data_from_loop(self):
        return [self.program_tracker.gather_session(), self.mouse_tracker.gather_session(), self.keyboard_tracker.gather_session()]

    def report_loop_to_db(self, loop_content):
        self.db.record(loop_content)
    
    def cleanup(self):  # Add this method to ProductivityTracker
        """Clean up resources before exit."""
        print("cleaning up")
        # TODO: Set the while loop's condiitons to False
        self.mouse_tracker.stop()
        self.keyboard_tracker.stop()
        self.program_tracker.stop()  # TODO: implement