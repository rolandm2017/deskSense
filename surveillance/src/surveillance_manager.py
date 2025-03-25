# surveillance/src/surveillance_manager.py
from pathlib import Path

import asyncio
import zmq
import traceback
import zmq.asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from datetime import datetime


from .arbiter.activity_arbiter import ActivityArbiter

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
from .object.classes import ProgramSessionData
from .services.chrome_service import ChromeService
from .trackers.mouse_tracker import MouseTrackerCore
from .trackers.keyboard_tracker import KeyboardTrackerCore
from .trackers.program_tracker import ProgramTrackerCore
from .util.detect_os import OperatingSystemInfo
from .util.clock import SystemClock, UserFacingClock
from .util.threaded_tracker import ThreadedTracker


class FacadeInjector:
    def __init__(self, keyboard, mouse, program) -> None:
        self.get_keyboard_facade_instance = keyboard
        self.get_mouse_facade_instance = mouse
        self.program_facade = program  # must receive OS arg


class SurveillanceManager:
    def __init__(self, session_maker: async_sessionmaker, shutdown_session_maker: sessionmaker, chrome_service, arbiter: ActivityArbiter, facades, shutdown_signal=None):
        """
        Facades argument is DI for testability.
        """
        self.session_maker = session_maker
        self.chrome_service = chrome_service

        self.arbiter = arbiter
        # Initialize tracking data
        self.current_window = None
        self.start_time = None
        self.session_data = []

        self.message_receiver = MessageReceiver("tcp://127.0.0.1:5555")

        current_os = OperatingSystemInfo()

        keyboard_facade = facades.get_keyboard_facade_instance()
        mouse_facade = facades.get_mouse_facade_instance()
        program_facade = facades.program_facade(current_os)

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

        self.keyboard_tracker = KeyboardTrackerCore(
            keyboard_facade, self.handle_keyboard_ready_for_db)
        self.mouse_tracker = MouseTrackerCore(
            mouse_facade, self.handle_mouse_ready_for_db)
        self.operate_facades()
        # Program tracker
        self.program_tracker = ProgramTrackerCore(
            clock, program_facade, self.handle_window_change, self.handle_program_ready_for_db)
        

        if current_os.is_windows:
            from .trackers.windows_system_tracker import WindowsSystemPowerTracker
            self.system_tracker = WindowsSystemPowerTracker(self.shutdown_handler, system_status_dao, self.check_session_integrity)
        else:
            self.system_tracker = None
            # from .trackers.ubuntu_system_tracker import UbuntuSystemPowerTracker
            # self.system_tracker = UbuntuSystemPowerTracker(
                # self.shutdown_handler, system_status_dao, self.check_session_integrity)

        self.keyboard_thread = ThreadedTracker(self.keyboard_tracker)
        self.mouse_thread = ThreadedTracker(self.mouse_tracker)
        self.program_thread = ThreadedTracker(self.program_tracker)

    def start_trackers(self):
        self.is_running = True
        self.keyboard_thread.start()
        self.mouse_thread.start()
        self.program_thread.start()

    def operate_facades(self):
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
        print(event, type(event), "153ru")
        # assert isinstance(event, ProgramSessionData)
        self.loop.create_task(self.arbiter.set_program_state(event))

    # FIXME: Am double counting for sure
    def handle_program_ready_for_db(self, event):
        self.loop.create_task(self.program_dao.create(event))

    def handle_chrome_ready_for_db(self, event):
        pass  # lives in Chrome Service

    async def shutdown_handler(self):
        try:
            await self.chrome_service.shutdown()  # works despite the lack of highlighting
            await self.arbiter.shutdown()
            await self.program_summary_dao.shutdown()
            await self.chrome_summary_dao.shutdown()
        except Exception as e:
            print(self.chrome_service,  " none?")
            traceback.print_exc()
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
