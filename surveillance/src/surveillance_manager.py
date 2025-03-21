# surveillance/src/surveillance_manager.py
from pathlib import Path

import asyncio
import zmq
import zmq.asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from datetime import datetime


from .arbiter.activity_arbiter import ActivityArbiter


from .facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance
from .facade.keyboard_facade import KeyboardFacadeCore
from .facade.mouse_facade import MouseFacadeCore
from .facade.program_facade import ProgramApiFacadeCore
from .facade.receive_messages import MessageReceiver

from .db.dao.system_status_dao import SystemStatusDao
from .db.dao.session_integrity_dao import SessionIntegrityDao


from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.program_dao import ProgramDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao
from .services.chrome_service import ChromeService
from .trackers.mouse_tracker import MouseTrackerCore
from .trackers.keyboard_tracker import KeyboardTrackerCore
from .trackers.program_tracker import ProgramTrackerCore
from .trackers.system_tracker import SystemPowerTracker
from .util.detect_os import OperatingSystemInfo
from .util.clock import SystemClock, UserFacingClock
from .util.threaded_tracker import ThreadedTracker

# from .keyboard_tracker import KeyActivityTracker


class SurveillanceManager:
    def __init__(self, session_maker: async_sessionmaker, shutdown_session_maker: sessionmaker, chrome_service, arbiter, shutdown_signal=None):
        self.session_maker = session_maker
        self.chrome_service = chrome_service

        self.arbiter = arbiter
        # Initialize tracking data
        self.current_window = None
        self.start_time = None
        self.session_data = []

        self.message_receiver = MessageReceiver("tcp://127.0.0.1:5555")

        # Get the project root (parent of src directory)
        # This gets us surveillance/src/productivity_tracker.py
        current_file = Path(__file__)
        project_root = current_file.parent.parent  # Goes up two levels to surveillance/

        self.data_dir = project_root / 'productivity_logs'
        self.data_dir.mkdir(exist_ok=True)

        current_os = OperatingSystemInfo()

        keyboard_facade = get_keyboard_facade_instance()
        # TODO: choose the mouseApi facade based on OS
        mouse_facade = get_mouse_facade_instance()
        program_facade = ProgramApiFacadeCore(current_os)

        self.loop = asyncio.get_event_loop()
        clock = UserFacingClock()

        program_summary_logger = ProgramLoggingDao(self.session_maker)
        chrome_summary_logger = ChromeLoggingDao(self.session_maker)

        self.session_integrity_dao = SessionIntegrityDao(
            program_summary_logger, chrome_summary_logger, self.session_maker)
        system_status_dao = SystemStatusDao(
            self.session_maker, shutdown_session_maker)

        self.mouse_dao = MouseDao(self.session_maker)
        self.keyboard_dao = KeyboardDao(self.session_maker)
        self.program_dao = ProgramDao(self.session_maker)
        self.chrome_dao = ChromeDao(self.session_maker)

        self.program_summary_dao = ProgramSummaryDao(
            program_summary_logger, self.session_maker)
        self.chrome_summary_dao = ChromeSummaryDao(
            chrome_summary_logger, self.session_maker)

        self.timeline_dao = TimelineEntryDao(self.session_maker)

        # Register handlers for different event types
        self.message_receiver.register_handler(
            "keyboard", keyboard_facade.handle_keyboard_message)
        self.message_receiver.register_handler(
            "mouse", mouse_facade.handle_mouse_message)

        self.operate_facade()

        self.keyboard_tracker = KeyboardTrackerCore(
            clock, keyboard_facade, self.handle_keyboard_ready_for_db)
        self.mouse_tracker = MouseTrackerCore(
            clock, mouse_facade, self.handle_mouse_ready_for_db)
        # Program tracker
        self.program_tracker = ProgramTrackerCore(
            clock, program_facade, self.handle_window_change, self.handle_program_ready_for_db)
        #
        self.system_tracker = SystemPowerTracker(
            self.shutdown_handler, system_status_dao, self.check_session_integrity)

        self.keyboard_thread = ThreadedTracker(self.keyboard_tracker)
        self.mouse_thread = ThreadedTracker(self.mouse_tracker)
        self.program_thread = ThreadedTracker(self.program_tracker)

        # self.key_tracker = KeyActivityTracker(self.data_dir)

    def start_trackers(self):
        self.is_running = True
        self.keyboard_thread.start()
        self.mouse_thread.start()
        self.program_thread.start()

    def operate_facade(self):
        """Start the message receiver."""
        print("[info] message receiver starting")
        self.message_receiver.start()

    def check_session_integrity(self, latest_shutdown_time: datetime | None, latest_startup_time: datetime):
        # FIXME: get latest times from system status dao
        if latest_shutdown_time is None:
            self.loop.create_task(
                self.session_integrity_dao.audit_first_startup(latest_startup_time))
        else:
            self.loop.create_task(self.session_integrity_dao.audit_sessions(
                latest_shutdown_time, latest_startup_time))

    def handle_keyboard_ready_for_db(self, event):
        self.loop.create_task(
            self.timeline_dao.create_from_keyboard_aggregate(event))
        self.loop.create_task(self.keyboard_dao.create(event))

    def handle_mouse_ready_for_db(self, event):
        self.loop.create_task(
            self.timeline_dao.create_from_mouse_move_window(event))
        self.loop.create_task(self.mouse_dao.create_from_window(event))

    def handle_window_change(self, event):
        self.loop.create_task(self.arbiter.set_program_state(event))

    # FIXME: Am double counting for sure
    def handle_program_ready_for_db(self, event):
        self.loop.create_task(self.program_dao.create(event))

    def handle_chrome_ready_for_db(self, event):
        pass  # lives in Chrome Service

    async def shutdown_handler(self):
        try:
            # TODO: Add Program Summary DAO shutdown -> prevent alt tab window being huge
            await self.chrome_service.shutdown()  # works despite the lack of highlighting
            await self.arbiter.shutdown()
            await self.program_summary_dao.shutdown()
            # TODO: Add Chrome Summary DAO shutdown -> similar reasons
            await self.chrome_summary_dao.shutdown()
        except Exception as e:
            print(f"Error during shutdown cleanup: {e}")

    async def cleanup(self):
        """Clean up resources before exit."""
        print("cleaning up")
        self.keyboard_thread.stop()
        self.mouse_thread.stop()
        self.program_thread.stop()

        await self.message_receiver.async_stop()

        self.is_running = False
        # Add any async cleanup operations here
        await asyncio.sleep(0.5)  # Give threads time to clean up
