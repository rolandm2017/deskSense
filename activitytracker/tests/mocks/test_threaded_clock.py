import unittest
import threading
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from activitytracker.util.time_wrappers import UserLocalTime
from tests.mocks.mock_clock import UserLocalTimeMockClock


class MockedSession:
    """A simplified mock session for testing"""

    def __init__(self):
        self.id = "test_session"


class MockedDao:
    """A simulated DAO that uses the clock"""

    def __init__(self, clock):
        self.user_facing_clock = clock
        self.call_count = 0

    def add_ten_sec_to_end_time(self, session):
        """Simulates the actual method that's causing issues"""
        # Get current time from clock
        now = self.user_facing_clock.now()
        self.call_count += 1
        return now


class SimplifiedKeepAliveEngine:
    """Simplified version of your KeepAliveEngine"""

    def __init__(self, session, dao):
        self.session = session
        self.dao = dao
        self.elapsed = 0

    def iterate_loop(self):
        self.elapsed += 1
        if self.elapsed >= 3:  # Simplified logic
            self._pulse_add_ten()
            self.elapsed = 0

    def _pulse_add_ten(self):
        self.dao.add_ten_sec_to_end_time(self.session)


class SimplifiedThreadedContainer:
    """Simplified version of your ThreadedEngineContainer"""

    def __init__(self, engine, interval=0.01):
        self.engine = engine
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._iterate_loop)
        self.thread.daemon = True
        self.thread.start()

    def _iterate_loop(self):
        iteration_count = 0
        while not self.stop_event.is_set() and iteration_count < 20:
            self.engine.iterate_loop()
            time.sleep(self.interval)
            iteration_count += 1  # Safety limit for test

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)


class TestMockClockThreading(unittest.TestCase):
    def test_threading_issue(self):
        """Test that simulates your specific threading setup"""
        # Create a list of 7 times (deliberately fewer than needed)
        times = [
            UserLocalTime(datetime(2025, 3, 22, 16, 14, i, tzinfo=timezone.utc))
            for i in range(7)
        ]

        # Create our mock clock with detailed debugging
        clock = UserLocalTimeMockClock(times)

        # Add thread ID to debug output
        original_now = clock.now

        def now_with_thread_id():
            thread_id = threading.get_ident()
            print(f"[THREAD DEBUG] Clock call from thread {thread_id}")
            return original_now()

        clock.now = now_with_thread_id

        # Create the DAO that will use the clock
        dao = MockedDao(clock)

        # Set up the engine and thread container
        session = MockedSession()
        engine = SimplifiedKeepAliveEngine(session, dao)
        container = SimplifiedThreadedContainer(engine)

        # Also track direct calls from main thread
        direct_calls = []
        for i in range(3):
            time_value = clock.now()
            direct_calls.append(time_value)
            time.sleep(0.02)  # Small delay

        # Start the background thread
        container.start()

        # Wait a bit for the thread to run
        time.sleep(0.2)

        # Make some more direct calls
        for i in range(2):
            time_value = clock.now()
            direct_calls.append(time_value)
            time.sleep(0.02)

        # Stop the thread
        container.stop()

        # Check results
        print(f"Direct calls count: {len(direct_calls)}")
        print(f"DAO calls count: {dao.call_count}")
        print(f"Total clock count: {clock.count_of_times}")

        # This will fail if we have the threading issue
        self.assertEqual(
            clock.count_of_times,
            len(direct_calls) + dao.call_count,
            "Clock count doesn't match expected number of calls",
        )
