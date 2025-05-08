# mock_clock.py
import inspect
import threading
from zoneinfo import ZoneInfo

from datetime import datetime, timedelta, timezone

from typing import Iterator

from activitytracker.config.definitions import local_time_zone
from activitytracker.util.clock import ClockProtocol
from activitytracker.util.time_wrappers import UserLocalTime


class MockClock(ClockProtocol):
    def __init__(self, times: list[datetime] | Iterator[datetime]):
        value_for_iter = iter(times) if isinstance(times, list) else times
        self.times = value_for_iter
        self.count_of_times = 0
        self._current_time = None

    def now(self) -> datetime:
        try:
            next_val_from_iter = next(self.times)
            self._current_time = next_val_from_iter
            if self._current_time.tzinfo is None:
                self._current_time = self._current_time.replace(tzinfo=timezone.utc)
            # print("[debug] Returning ", self._current_time, datetime.now().strftime("%I:%M:%S %p"))
            self.count_of_times += 1
            return self._current_time

        except StopIteration:
            raise RuntimeError(
                f"MockClock ran out of times. It started with {self.count_of_times}"
            )

    def seconds_have_elapsed(
        self, current_time: datetime, previous_time: datetime, seconds: int
    ) -> bool:
        """Check if the specified number of seconds has elapsed between two times."""
        elapsed = current_time - previous_time
        return elapsed >= timedelta(seconds=seconds)

    def advance_time(self, n: int):
        """
        Advance the iterator by n positions.
        Example: self.times is [3, 4, 15, 16, 28, 29]
        next(self.times) would grab 3.
        advance_time(3) is called.
        3 -> 4 -> 15 -> 16 is 3 skips. next(self.times) grabs 28.
        """

        for position in range(n):
            self._current_time = next(self.times)

    def today_start(self):
        prev_current_time = self._current_time
        if prev_current_time:
            return prev_current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            new_time = self.now()
            return new_time.replace(hour=0, minute=0, second=0, microsecond=0)
        # return datetime.now(ZoneInfo(local_time_zone)).replace(
        #     hour=0, minute=0, second=0, microsecond=0)
        # Use self._current_time instead of datetime.now()


class UserLocalTimeMockClock(ClockProtocol):
    def __init__(self, times: list[UserLocalTime] | Iterator[UserLocalTime]):
        # Store the original times list or convert iterator to list
        if isinstance(times, list):
            self.original_times = times.copy()  # Make a copy to avoid modifying original
        else:
            self.original_times = list(times)  # Convert iterator to list

        if not self.original_times:
            raise ValueError("Cannot create MockClock with empty times list")

        # Create initial iterator
        self.times = iter(self.original_times)
        self.count_of_times = 0
        self._current_time = None

        # Thread safety lock
        self._lock = threading.RLock()

        # Debug info
        self.thread_call_counts = {}  # Track calls per thread

    def now(self) -> UserLocalTime:
        thread_id = threading.get_ident()

        # Get caller information
        stack = inspect.stack()
        caller_frame = stack[1]
        caller_function = caller_frame.function
        caller_filename = caller_frame.filename.split("\\")[-1]
        caller_line = caller_frame.lineno

        # Thread-safe increment and iterator access
        with self._lock:
            # Update thread call counts
            if thread_id not in self.thread_call_counts:
                self.thread_call_counts[thread_id] = 0
            self.thread_call_counts[thread_id] += 1

            try:
                # Try to get next value
                next_val_from_iter = next(self.times)
                self._current_time = next_val_from_iter

                # Ensure timezone is set
                if self._current_time.tzinfo is None:
                    self._current_time = self._current_time.replace(tzinfo=timezone.utc)

                # Increment counter safely
                self.count_of_times += 1

                # Debug output with thread info. Do not remove this. Commenting out is fine
                print(
                    f"[DEBUG] Clock call #{self.count_of_times} - Thread {thread_id} - "
                    f"Called by: {caller_filename}:{caller_function}:{caller_line}"
                )

                return self._current_time

            except StopIteration:
                # We're out of values, reset the iterator to reuse values
                print(
                    f"\n[WARNING] Clock ran out after {self.count_of_times} calls, resetting iterator"
                )
                self.times = iter(self.original_times)  # Reset iterator

                # Try again with the reset iterator
                next_val_from_iter = next(self.times)
                self._current_time = next_val_from_iter

                if self._current_time.tzinfo is None:
                    self._current_time = self._current_time.replace(tzinfo=timezone.utc)

                self.count_of_times += 1
                # Do not remove this. Commenting out is fine
                print(
                    f"[DEBUG] Clock RESET - call #{self.count_of_times} - Thread {thread_id} - "
                    f"Called by: {caller_filename}:{caller_function}:{caller_line}"
                )

                return self._current_time
            #  raise RuntimeError(
            #     f"MockClock ran out of times. It started with {self.count_of_times}")

    def seconds_have_elapsed(
        self, current_time: UserLocalTime, previous_time: UserLocalTime, seconds: int
    ) -> bool:
        """Check if the specified number of seconds has elapsed between two times."""
        elapsed = current_time.dt - previous_time.dt
        return elapsed >= timedelta(seconds=seconds)

    def advance_time(self, n: int):
        """
        Advance the iterator by n positions.
        Thread-safe version.
        """
        with self._lock:
            for position in range(n):
                try:
                    self._current_time = next(self.times)
                except StopIteration:
                    # Reset if we run out during advance
                    self.times = iter(self.original_times)
                    self._current_time = next(self.times)

    def today_start(self):
        """Thread-safe version of today_start"""
        # Get debug info
        thread_id = threading.get_ident()
        stack = inspect.stack()
        caller_frame = stack[1]
        caller_function = caller_frame.function
        caller_filename = caller_frame.filename.split("\\")[-1]
        caller_line = caller_frame.lineno

        print(
            f"[DEBUG] Clock today_start() - Thread {thread_id} - "
            f"Called by: {caller_filename}:{caller_function}:{caller_line}"
        )

        with self._lock:
            if self._current_time:
                return self._current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # This will call now() which increments counter
                new_time = self.now()
                return new_time.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_debug_info(self):
        """Return debug information about clock usage"""
        with self._lock:
            return {
                "total_calls": self.count_of_times,
                "calls_per_thread": self.thread_call_counts.copy(),
                "original_times_count": len(self.original_times),
            }
