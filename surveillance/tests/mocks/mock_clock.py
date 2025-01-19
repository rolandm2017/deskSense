# mock_clock.py
from datetime import datetime, timedelta
from typing import Iterator

from src.util.clock import ClockProtocol

class MockClock(ClockProtocol):
    def __init__(self, times: list[datetime] | Iterator[datetime]):
        self.times = iter(times) if isinstance(times, list) else times
        self._current_time = None

    def now(self) -> datetime:
        if self._current_time is not None:
            return self._current_time
        try:
            self._current_time = next(self.times)
            return self._current_time
        except StopIteration:
            raise RuntimeError("MockClock ran out of times")

    def has_elapsed_since(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        """Check if the specified number of seconds has elapsed between two times."""
        elapsed = current_time - previous_time
        return elapsed >= timedelta(seconds=seconds)

    def advance_time(self, seconds: int):
        """Advance the clock by specified number of seconds."""
        print(self._current_time, seconds, '25ru')
        if self._current_time is None:
            self._current_time = self.now()
        self._current_time += timedelta(seconds=seconds)
        print(self._current_time, '29ru')