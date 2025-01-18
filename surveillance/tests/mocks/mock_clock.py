from datetime import datetime
from typing import Iterator

class ClockProtocol:
    def now(self) -> datetime:
        raise NotImplementedError

class MockClock(ClockProtocol):
    def __init__(self, times: list[datetime] | Iterator[datetime]):
        self.times = iter(times) if isinstance(times, list) else times

    def now(self) -> datetime:
        try:
            return next(self.times)
        except StopIteration:
            raise RuntimeError("MockClock ran out of times")