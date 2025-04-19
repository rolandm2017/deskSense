# surveillance/src/surveillance_manager.py
from pathlib import Path

import asyncio
import traceback

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from datetime import datetime


from .arbiter.activity_arbiter import ActivityArbiter

from .facade.receive_messages import MessageReceiver

from .db.dao.direct.system_status_dao import SystemStatusDao
from .db.dao.direct.session_integrity_dao import SessionIntegrityDao

from .db.dao.queuing.mouse_dao import MouseDao
from .db.dao.queuing.keyboard_dao import KeyboardDao

from .db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from .db.dao.direct.program_summary_dao import ProgramSummaryDao
from .db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from .db.dao.queuing.program_logs_dao import ProgramLoggingDao
from .db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from .object.classes import ProgramSessionData
from .services.chrome_service import ChromeService
from .trackers.mouse_tracker import MouseTrackerCore
from .trackers.keyboard_tracker import KeyboardTrackerCore
from .trackers.program_tracker import ProgramTrackerCore
from .util.detect_os import OperatingSystemInfo
from .util.clock import SystemClock, UserFacingClock
from .util.threaded_tracker import ThreadedTracker
from surveillance.src.util.copy_util import snapshot_obj_for_tests


class FacadeInjector:
    def __init__(self, keyboard, mouse, program) -> None:
        self.get_keyboard_facade_instance = keyboard
        self.get_mouse_facade_instance = mouse
        self.program_facade = program  # must receive OS arg


class SurveillanceManager:
    def __init__(self, clock: UserFacingClock, async_session_maker: async_sessionmaker, regular_session_maker: sessionmaker, chrome_service, arbiter: ActivityArbiter, facades, shutdown_signal=None):
        """
        Facades argument is DI for testability.
        """
        self.is_running = False
        self.async_session_maker = async_session_maker
        self.regular_session = regular_session_maker
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

        program_summary_logger = ProgramLoggingDao(
            self.regular_session, self.async_session_maker)
        chrome_summary_logger = ChromeLoggingDao(
            self.regular_session, self.async_session_maker)

        self.session_integrity_dao = SessionIntegrityDao(
            program_summary_logger, chrome_summary_logger, self.async_session_maker)
        # FIXME: 04/04/2025: why isn't the sys status dao used anywhere?
        system_status_dao = SystemStatusDao(
            self.async_session_maker, self.regular_session)

        self.mouse_dao = MouseDao(self.async_session_maker)
        self.keyboard_dao = KeyboardDao(self.async_session_maker)
        # self.program_dao = ProgramDao(self.async_session_maker)
        # self.chrome_dao = ChromeDao(self.async_session_maker)

        self.program_summary_dao = ProgramSummaryDao(
            program_summary_logger, self.regular_session, self.async_session_maker)
        self.chrome_summary_dao = ChromeSummaryDao(
            chrome_summary_logger, self.regular_session, self.async_session_maker)

        self.timeline_dao = TimelineEntryDao(self.async_session_maker)

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

        self.keyboard_thread = ThreadedTracker(self.keyboard_tracker)
        self.mouse_thread = ThreadedTracker(self.mouse_tracker)
        self.program_thread = ThreadedTracker(self.program_tracker)

    def start_trackers(self):
        self.is_running = True
        print("Running trackers")
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
        # Deep copy to enable testing of object state before/after this line
        copy_of_event = snapshot_obj_for_tests(event)
        self.arbiter.set_program_state(copy_of_event)

    def handle_program_ready_for_db(self, event):
        pass
        # self.loop.create_task(self.program_dao.create(event))

    def shutdown_handler(self):
        try:
            self.chrome_service.shutdown()  # works despite the lack of highlighting
            self.arbiter.shutdown()
        except Exception as e:
            print(self.chrome_service,  " none?")
            traceback.print_exc()
            print(f"Error during shutdown cleanup: {e}")

    async def cancel_pending_tasks(self):
        """Safely cancel all pending tasks created by this manager."""
        # # Get all tasks from the event loop
        # tasks = [task for task in asyncio.all_tasks(self.loop)
        #          if task is not asyncio.current_task(self.loop)]

        # Create a set of tasks we know are created by this manager
        manager_tasks = set()

        # Track tasks from different components
        for attr_name in ['keyboard_dao', 'mouse_dao', 'timeline_dao',
                          'program_summary_dao', 'chrome_summary_dao',
                          'session_integrity_dao']:
            if hasattr(self, attr_name):
                component = getattr(self, attr_name)
                # Look for any attributes that might be tasks
                for name in dir(component):
                    if name.startswith('_task_') or name.endswith('_task'):
                        task = getattr(component, name, None)
                        if task and isinstance(task, asyncio.Task) and not task.done():
                            manager_tasks.add(task)

        # Cancel all identified tasks
        if manager_tasks:
            print(f"Cancelling {len(manager_tasks)} pending tasks...")
            for task in manager_tasks:
                task.cancel()

            # Wait for all tasks to complete with a timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*manager_tasks, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                print("Some tasks didn't complete within timeout")

        return len(manager_tasks)

    async def cleanup(self):
        """Clean up resources before exit."""
        print("cleaning up")
        self.keyboard_thread.stop()
        self.mouse_thread.stop()
        self.program_thread.stop()

        # Cancel any pending database tasks first
        await self.cancel_pending_tasks()

        # Then stop the message receiver
        if hasattr(self, 'message_receiver') and self.message_receiver:
            try:
                await self.message_receiver.async_stop()
            except Exception as e:
                print(f"Error during MessageReceiver cleanup: {e}")
                traceback.print_exc()

        self.is_running = False
        # Add any async cleanup operations here
        await asyncio.sleep(0.5)  # Give threads time to clean up
