from datetime import datetime
from typing import Iterator

class ClockProtocol:
    def now(self) -> datetime:
        raise NotImplementedError

class Clock(ClockProtocol):
    def now(self) -> datetime:
        return datetime.now()


