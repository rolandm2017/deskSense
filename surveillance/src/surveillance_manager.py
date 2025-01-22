from pathlib import Path

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker


from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.program_dao import ProgramDao
from .db.dao.daily_summary_dao import DailySummaryDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .trackers.mouse_tracker import MouseTrackerCore
from .trackers.keyboard_tracker import KeyboardTrackerCore
from .trackers.program_tracker import ProgramTrackerCore
from .facade.keyboard_facade import KeyboardApiFacadeCore
from .facade.mouse_facade import MouseApiFacade, UbuntuMouseApiFacadeCore
from .facade.program_facade import ProgramApiFacadeCore
from .util.interrupt_handler import InterruptHandler
from .util.detect_os import OperatingSystemInfo
from .util.clock import Clock
from .util.threaded_tracker import ThreadedTracker
# from .keyboard_tracker import KeyActivityTracker


# TODO: Report mouse, keyboard, program, chrome tabs, every 10 sec, to the db.
# TODO: report only closed loops of mouse, if unclosed, move to next cycle


class SurveillanceManager:
    def __init__(self, session_maker: async_sessionmaker, shutdown_signal=None):
        self.session_maker = session_maker
        # Initialize tracking data
        self.current_window = None
        self.start_time = None
        self.session_data = []

        # Get the project root (parent of src directory)
        # This gets us surveillance/src/productivity_tracker.py
        current_file = Path(__file__)
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/

        self.data_dir = project_root / 'productivity_logs'
        self.data_dir.mkdir(exist_ok=True)

        current_os = OperatingSystemInfo()

        keyboard_facade = KeyboardApiFacadeCore()
        # TODO: choose the mouseApi facade based on OS
        mouse_facade = UbuntuMouseApiFacadeCore()
        program_facade = ProgramApiFacadeCore(current_os)

        self.loop = asyncio.get_event_loop()
        self.mouse_dao = MouseDao(self.session_maker)
        self.summary_dao = DailySummaryDao(self.session_maker)
        self.timeline_dao = TimelineEntryDao(self.session_maker)
        self.keyboard_dao = KeyboardDao(self.session_maker)
        self.program_dao = ProgramDao(self.session_maker)
        self.chrome_dao = ChromeDao(self.session_maker)

        clock = Clock()

        self.keyboard_tracker = KeyboardTrackerCore(
            clock, keyboard_facade, self.handle_keyboard_ready_for_db)
        self.mouse_tracker = MouseTrackerCore(
            clock, mouse_facade, self.handle_mouse_ready_for_db)
        self.program_tracker = ProgramTrackerCore(
            clock, program_facade, self.handle_program_ready_for_db)

        self.keyboard_thread = ThreadedTracker(self.keyboard_tracker)
        self.mouse_thread = ThreadedTracker(self.mouse_tracker)
        self.program_thread = ThreadedTracker(self.program_tracker)
        # self.key_tracker = KeyActivityTracker(self.data_dir)

        # TODO: Wrap the Cores in the Threaders
        # TODO: Start the threaders
        # TODO: Update shutdown "stop" stuff
        # TODO: Test the API endpoints, integration, from DB to response

    def start_trackers(self):
        self.is_running = True
        self.keyboard_thread.start()
        self.mouse_thread.start()
        self.program_thread.start()

    def handle_keyboard_ready_for_db(self, event):
        self.loop.create_task(
            self.timeline_dao.create_from_keyboard_aggregate(event))
        self.loop.create_task(self.keyboard_dao.create(event))

    def handle_mouse_ready_for_db(self, event):
        self.loop.create_task(
            self.timeline_dao.create_from_mouse_move_window(event))
        self.loop.create_task(self.mouse_dao.create_from_window(event))

    def handle_program_ready_for_db(self, event):
        self.loop.create_task(
            self.summary_dao.create_if_new_else_update(event))
        self.loop.create_task(self.program_dao.create(event))

    def cleanup(self):  # Add this method to ProductivityTracker
        """Clean up resources before exit."""
        print("cleaning up")
        self.keyboard_thread.stop()
        self.mouse_thread.stop()
        self.program_thread.stop()
        self.is_running = False
