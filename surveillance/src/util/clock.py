# clock.py
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from typing import Iterator

from ..config.definitions import local_time_zone


class ClockProtocol:
    def now(self) -> datetime:
        raise NotImplementedError

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        raise NotImplementedError


class SystemClock(ClockProtocol):
    def now(self) -> datetime:
        # Returns the current time in UTC:
        # The server always uses UTC!
        return datetime.now(timezone.utc)

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        elapsed = current_time - previous_time
        return elapsed >= timedelta(seconds=seconds)


class UserFacingClock(ClockProtocol):
    def now(self) -> datetime:
        return datetime.now(ZoneInfo(local_time_zone))
        # return datetime.now()

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        elapsed = current_time - previous_time
        return elapsed >= timedelta(seconds=seconds)

    def get_start_of_week(self, user_tz, date):
        pass

    def get_previous_sunday(self, date=None):
        """Get the most recent Sunday before the given date (or today)"""
        target = date or self.now()
        days_since_sunday = (target.weekday() + 1) % 7
        return target - timedelta(days=days_since_sunday)

    def get_day_start(self, date=None):
        """Get midnight for the specified day"""
        target = date or self.now()
        return datetime.combine(target.date(), datetime.min.time())
