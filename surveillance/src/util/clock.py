# clock.py
from typing import Iterator
from datetime import datetime, timedelta, timezone


class ClockProtocol:
    def now(self) -> datetime:
        raise NotImplementedError

    def has_elapsed_since(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        raise NotImplementedError


class SystemClock(ClockProtocol):
    def now(self) -> datetime:
        # Returns the current time in UTC:
        # The server always uses UTC!
        return datetime.now(timezone.utc)

    def has_elapsed_since(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        elapsed = current_time - previous_time
        return elapsed >= timedelta(seconds=seconds)


class UserFacingClock(ClockProtocol):
    def now(self) -> datetime:
        return datetime.now()

    def get_start_of_week(self, user_tz, date):
        pass
