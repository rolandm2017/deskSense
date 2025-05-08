# activitytracker/src/surveillance_manager.py
import traceback
from pathlib import Path

import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from datetime import datetime

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.session_integrity_dao import SessionIntegrityDao
from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.keyboard_dao import KeyboardDao
from activitytracker.db.dao.queuing.mouse_dao import MouseDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.facade.receive_messages import MessageReceiver
from activitytracker.trackers.keyboard_tracker import KeyboardTrackerCore
from activitytracker.trackers.mouse_tracker import MouseTrackerCore
from activitytracker.trackers.program_tracker import ProgramTrackerCore
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.copy_util import snapshot_obj_for_tests
from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.util.periodic_task import AsyncPeriodicTask
from activitytracker.util.threaded_tracker import ThreadedTracker


class FacadeInjector:
    def __init__(self, keyboard, mouse, program) -> None:
        self.get_keyboard_facade_instance = keyboard
        self.get_mouse_facade_instance = mouse
        self.program_facade = program  # must receive OS arg


class SurveillanceManager:
    def __init__(
        self,
        clock: UserFacingClock,
        async_session_maker: async_sessionmaker,
        regular_session_maker: sessionmaker,
        chrome_service,
        arbiter: ActivityArbiter,
        facades,
        message_receiver: MessageReceiver,
    ):
        """
        Facades argument is DI for testability.
        """
        self.is_running = False
        self.async_session_maker = async_session_maker
        self.regular_session = regular_session_maker
        self.chrome_service = chrome_service

        self.arbiter = arbiter

        self.message_receiver = message_receiver
        # self.message_receiver = MessageReceiver("tcp://127.0.0.1:5555")

        current_os = OperatingSystemInfo()

        keyboard_facade = facades.get_keyboard_facade_instance()
        mouse_facade = facades.get_mouse_facade_instance()
        program_facade = facades.program_facade(current_os)

        self.loop = asyncio.get_event_loop()

        program_summary_logger = ProgramLoggingDao(self.regular_session)
        chrome_summary_logger = ChromeLoggingDao(self.regular_session)

        self.session_integrity_dao = SessionIntegrityDao(
            program_summary_logger, chrome_summary_logger, self.async_session_maker
        )

        self.system_status_dao = SystemStatusDao(clock, self.regular_session)

        self.program_online_polling = AsyncPeriodicTask(self.system_status_dao)
        self.program_online_polling.start()

        self.mouse_dao = MouseDao(self.async_session_maker)
        self.keyboard_dao = KeyboardDao(self.async_session_maker)
        # self.program_dao = ProgramDao(self.async_session_maker)
        # self.chrome_dao = ChromeDao(self.async_session_maker)

        self.program_summary_dao = ProgramSummaryDao(program_summary_logger, self.regular_session)
        self.chrome_summary_dao = ChromeSummaryDao(chrome_summary_logger, self.regular_session)

        self.timeline_dao = TimelineEntryDao(self.async_session_maker)

        # Register handlers for different event types
        self.message_receiver.register_handler(
            "keyboard", keyboard_facade.handle_keyboard_message
        )
        self.message_receiver.register_handler("mouse", mouse_facade.handle_mouse_message)

        self.keyboard_tracker = KeyboardTrackerCore(
            keyboard_facade, self.handle_keyboard_ready_for_db
        )
        self.mouse_tracker = MouseTrackerCore(mouse_facade, self.handle_mouse_ready_for_db)
        self.operate_facades()
        # Program tracker
        self.program_tracker = ProgramTrackerCore(
            clock, program_facade, self.handle_window_change
        )

        self.keyboard_thread = ThreadedTracker(self.keyboard_tracker)
        self.mouse_thread = ThreadedTracker(self.mouse_tracker)
        self.program_thread = ThreadedTracker(self.program_tracker)

        self.cancelled_tasks = 0

        self.logger = ConsoleLogger()

    def start_trackers(self):
        self.is_running = True
        print("Running trackers")
        self.keyboard_thread.start()
        self.mouse_thread.start()
        self.program_thread.start()

    def print_sys_status_info(self):
        latest_status = self.system_status_dao.read_latest()
        if latest_status is None:
            self.logger.log_yellow("No latest status found")
        else:
            time_string = latest_status.created_at.strftime("%m-%d %H:%M:%S")
            self.logger.log_white(f"[info] latest status {latest_status.status} at {time_string}")

    def operate_facades(self):
        """Start the message receiver."""
        print("[info] message receiver starting")
        self.message_receiver.start()

    def check_session_integrity(
        self, latest_shutdown_time: datetime | None, latest_startup_time: datetime
    ):
        # FIXME: This function isn't being used anywhere! And it still should be
        # FIXME: get latest times from system status dao
        if latest_shutdown_time is None:
            self.session_integrity_dao.audit_first_startup(latest_startup_time)
            # self.loop.create_task(
            #     self.session_integrity_dao.audit_first_startup(latest_startup_time))
        else:
            self.session_integrity_dao.audit_sessions(latest_shutdown_time, latest_startup_time)
            #     latest_shutdown_time, latest_startup_time)
            # self.loop.create_task(self.session_integrity_dao.audit_sessions(
            #     latest_shutdown_time, latest_startup_time))

    def handle_keyboard_ready_for_db(self, event):
        self.loop.create_task(self.timeline_dao.create_from_keyboard_aggregate(event))
        self.loop.create_task(self.keyboard_dao.create(event))

    def handle_mouse_ready_for_db(self, event):
        self.loop.create_task(self.timeline_dao.create_from_mouse_move_window(event))
        self.loop.create_task(self.mouse_dao.create_from_window(event))

    def handle_window_change(self, event):
        # Deep copy to enable testing of object state before/after this line
        copy_of_event = snapshot_obj_for_tests(event)
        self.arbiter.set_program_state(copy_of_event)  # type: ignore

    def shutdown_handler(self):
        try:
            self.chrome_service.shutdown()  # works despite the lack of highlighting
            self.arbiter.shutdown()
            self.program_online_polling.stop()
        except Exception as e:
            print(f"Error during shutdown cleanup: {e}")
            traceback.print_exc()

    async def cancel_pending_tasks(self):
        """Safely cancel all pending tasks created by this manager."""
        await self.program_online_polling.stop()
        # Get all tasks from the event loop except the current one
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task is not current_task]

        # Print detailed information about all tasks
        print(f"Found {len(all_tasks)} total asyncio tasks")

        # Look for uvicorn related tasks specifically
        uvicorn_tasks = []
        manager_tasks = []
        other_tasks = []

        for task in all_tasks:
            task_name = task.get_name()
            task_status = "DONE" if task.done() else "PENDING"

            # Try to get the frame information
            task_frame = None
            try:
                stack = task.get_stack()
                task_frame = stack[0] if stack else None
                frame_info = (
                    f"File: {task_frame.f_code.co_filename}, Line: {task_frame.f_lineno}"
                    if task_frame
                    else "Unknown"
                )
            except Exception:
                frame_info = "Not available"

            print(f"Task: {task_name} | Status: {task_status} | Source: {frame_info}")

            # Separate tasks by category for better handling
            if "uvicorn" in frame_info.lower() or "starlette" in frame_info.lower():
                uvicorn_tasks.append(task)
            elif any(
                indicator in task_name.lower()
                for indicator in [
                    "mouse",
                    "keyboard",
                    "program",
                    "timeline",
                    "chrome",
                    "dao",
                    "messagereceiver",
                ]
            ):
                manager_tasks.append(task)
            else:
                other_tasks.append(task)

        # Only cancel our manager tasks, not FastAPI framework tasks
        cancelled_count = 0
        if manager_tasks:
            print(f"\nCancelling {len(manager_tasks)} manager-related tasks:")
            for task in manager_tasks:
                if not task.done():
                    stack = task.get_stack()
                    task_frame = stack[0] if stack else None
                    frame_info = (
                        f"File: {task_frame.f_code.co_filename}, Line: {task_frame.f_lineno}"
                        if task_frame
                        else "Unknown"
                    )
                    print(f"Cancelling task: '{task.get_name()}' from '{frame_info}'")
                    task.cancel()
                    cancelled_count += 1

        # Log but don't cancel uvicorn tasks
        if uvicorn_tasks:
            print(f"\nFound {len(uvicorn_tasks)} uvicorn/starlette tasks (not cancelling):")
            for task in uvicorn_tasks:
                print(f"  - {task.get_name()}")

        # Try to safely wait for manager tasks to complete
        if manager_tasks:
            try:
                # Wait for all tasks to complete with a timeout
                await asyncio.wait_for(
                    asyncio.gather(*manager_tasks, return_exceptions=True), timeout=3.0
                )
            except asyncio.TimeoutError:
                print("Some tasks didn't complete within timeout")

        print(f"Cancelled {cancelled_count} tasks")
        return cancelled_count

    async def cleanup(self):
        """Clean up resources before exit."""
        print("cleaning up")

        # First stop the threads - this should be safe from exceptions
        try:
            self.keyboard_thread.stop()
            self.mouse_thread.stop()
            self.program_thread.stop()
            # Stop the asyncio loop
            await self.program_online_polling.stop()
        except Exception as e:
            print(f"Error stopping threads: {e}")

        # Store the count of canceled tasks
        cancelled_tasks = 0

        # Cancel any pending database tasks
        try:
            cancelled_tasks = await self.cancel_pending_tasks()
        except asyncio.CancelledError:
            print("Task cancellation was itself cancelled - continuing cleanup")
            cancelled_tasks = 0
        except Exception as e:
            print(f"Error canceling tasks: {e}")
            import traceback

            traceback.print_exc()

        # Then stop the message receiver
        if hasattr(self, "message_receiver") and self.message_receiver:
            try:
                await self.message_receiver.async_stop()
            except asyncio.CancelledError:
                print("MessageReceiver async_stop was cancelled - continuing shutdown")
            except Exception as e:
                print(f"Error during MessageReceiver cleanup: {e}")
                import traceback

                traceback.print_exc()

        self.is_running = False

        # Return the count for the caller
        return cancelled_tasks
