# mock_clock.py
from datetime import datetime, timedelta, timezone
from typing import Iterator

from zoneinfo import ZoneInfo

from surveillance.src.config.definitions import local_time_zone

from surveillance.src.util.clock import ClockProtocol
from surveillance.src.util.time_wrappers import UserLocalTime


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
                self._current_time = self._current_time.replace(
                    tzinfo=timezone.utc)
            # print("[debug] Returning ", self._current_time, datetime.now().strftime("%I:%M:%S %p"))
            self.count_of_times += 1
            return self._current_time
          
        except StopIteration:
            raise RuntimeError(
                f"MockClock ran out of times. It started with {self.count_of_times}")

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
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
        value_for_iter = iter(times) if isinstance(times, list) else times
        self.times = value_for_iter
        self.count_of_times = 0
        self._current_time = None

    def now(self) -> UserLocalTime:
        try:
            next_val_from_iter = next(self.times)
            self._current_time = next_val_from_iter
            try:
                if self._current_time.tzinfo is None:
                    self._current_time = self._current_time.replace(
                        tzinfo=timezone.utc)
                # print("[debug] Returning ", self._current_time, UserLocalTime.now().strftime("%I:%M:%S %p"))
                self.count_of_times += 1
                return self._current_time
            except AttributeError as e:
                print(f"After {self.count_of_times}, _current_time was None")
                print(e)
                raise
        except StopIteration:
            if self._current_time is not None:
                print(f"WARNING: MockClock ran out after {self.count_of_times} calls, reusing last time")
                self.count_of_times += 1
                return self._current_time
            else:
                raise RuntimeError(f"MockClock ran out of times and has no last time")
            # raise RuntimeError(
            #     f"MockClock ran out of times. It started with {self.count_of_times}")

    def seconds_have_elapsed(self, current_time: UserLocalTime, previous_time: UserLocalTime, seconds: int) -> bool:
        """Check if the specified number of seconds has elapsed between two times."""
        elapsed = current_time.dt - previous_time.dt
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
