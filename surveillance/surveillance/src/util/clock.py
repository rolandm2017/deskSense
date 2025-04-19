# clock.py
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from typing import Iterator

from surveillance.src.config.definitions import local_time_zone
from surveillance.src.util.time_formatting import get_start_of_day
from surveillance.src.util.time_wrappers import UserLocalTime


class ClockProtocol:
    def now(self) -> datetime:
        raise NotImplementedError

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        raise NotImplementedError

    def today(self) -> datetime:
        raise NotImplementedError

    def today_start(self) -> datetime:
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
    def __init__(self):
        self.today = get_start_of_day(self.now())

    def now(self) -> UserLocalTime:
        # utc_now = datetime.now(timezone.utc)

        # # Convert it to the local timezone explicitly
        # local_now = utc_now.astimezone(ZoneInfo(local_time_zone))

        # return local_now
        return UserLocalTime(datetime.now(ZoneInfo(local_time_zone)))

    def today(self):
        """
        If today hasn't changed, just return today.

        But if the program has run to long that .today now is yesterday, update it first.
        """
        # TODO: Make the code match the comment
        return self.today

    def today_start(self):
        return get_start_of_day(datetime.now(ZoneInfo(local_time_zone)))

    def seconds_have_elapsed(self, current_time: datetime, previous_time: datetime, seconds: int) -> bool:
        """
        Arguments dictate that the 1st arg is closer to the present than the 2nd arg.
        Alternatively: The 2nd arg happened further in the past than the 1st.
        """
        if current_time > previous_time:
            elapsed = current_time - previous_time
            return elapsed >= timedelta(seconds=seconds)
        else:
            raise ValueError("current_time must be later than previous_time.")

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

    def is_timezone_aware(self, dt):
        """
        Check if a datetime object has timezone information.

        Args:
            dt (datetime): The datetime object to check

        Returns:
            bool: True if the datetime has timezone info, False otherwise
        """
        return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

    def timezones_are_same(self, dt1, dt2):
        """
        Check if two datetime objects have the same timezone.
        Both datetimes must be timezone-aware for this comparison to be meaningful.

        Args:
            dt1 (datetime): First datetime object
            dt2 (datetime): Second datetime object

        Returns:
            bool: True if both datetimes have the same timezone, False otherwise

        Raises:
            ValueError: If either datetime is not timezone-aware
        """
        if not self.is_timezone_aware(dt1) or not self.is_timezone_aware(dt2):
            raise ValueError("Both datetime objects must be timezone-aware")

        # Compare the UTC offsets at the specific times
        return dt1.tzinfo.utcoffset(dt1) == dt2.tzinfo.utcoffset(dt2)
