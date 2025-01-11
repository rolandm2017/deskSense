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
from .program_tracker import ProgramTracker
# from .keyboard_tracker import KeyActivityTracker


# TODO: Report mouse, keyboard, program, chrome tabs, every 10 sec, to the db.
# TODO: report only closed loops of mouse, if unclosed, move to next cycle


class SurveillanceManager:
    def __init__(self, db_conn):
        self.db = db_conn
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

        self.program_tracker = ProgramTracker(self.data_dir)
        self.mouse_tracker = MouseTracker(self.data_dir)
        self.keyboard_tracker = KeyboardTracker(self.data_dir)
        # self.key_tracker = KeyActivityTracker(self.data_dir)
        # self.key_tracker.start()
    

    def gather_data_from_loop(self):
        return [self.program_tracker.gather_session(), self.mouse_tracker.gather_session(), self.keyboard_tracker.gather_session()]

    def report_loop_to_db(self, loop_content):
        self.db.record(loop_content)
    
    def cleanup(self):  # Add this method to ProductivityTracker
        """Clean up resources before exit."""
        self.mouse_tracker.stop()
        self.keyboard_tracker.stop()
        self.program_tracker.stop()  # TODO: implement