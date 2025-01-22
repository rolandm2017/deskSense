# mock_clock.py
from datetime import datetime, timedelta
from typing import Iterator


from src.util.clock import ClockProtocol


class MockClock(ClockProtocol):
    def __init__(self, times: list[datetime] | Iterator[datetime]):
        self.times = iter(times) if isinstance(times, list) else times
        self._current_time = None

    def now(self) -> datetime:
        try:
            self._current_time = next(self.times)
            print("[debug] Returning ", self._current_time)
            return self._current_time
        except StopIteration:
            raise RuntimeError("MockClock ran out of times")

    def has_elapsed_since(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
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
