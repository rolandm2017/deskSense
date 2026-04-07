"""
Thin newtype wrappers for timezone-aware datetimes.

The ONLY job of these classes is to answer:
    "Is this datetime in the user's local timezone, or in system/UTC time?"

They are NOT datetime replacements. They don't proxy attribute access,
override arithmetic, or implement comparison operators.
Instead, you unwrap with .dt when you need the real datetime.

    ult = UserLocalTime(some_tz_aware_datetime)
    ult.dt.date()           # explicit unwrap
    ult.dt + timedelta(1)   # returns a plain datetime — wrap again if needed

Rules of thumb:
    - Service/controller layer: pass UserLocalTime / SystemTime around
    - DAO layer: unwrap with .dt (Postgres only understands datetime)
    - Arithmetic: unwrap, compute, re-wrap
"""

from datetime import datetime

from activitytracker.util.errors import TimezoneUnawareError


class UserLocalTime:
    """
    A datetime known to be in the user's local timezone.

    Construct from a tz-aware datetime. Rejects naive datetimes at the door.
    Unwrap with .dt when you need the underlying datetime.
    """

    __slots__ = ("dt", "tzinfo",)

    def __init__(self, dt):
        if isinstance(dt, UserLocalTime):
            self.dt = dt.dt
        elif not isinstance(dt, datetime):
            raise TypeError(
                f"UserLocalTime expects a datetime, got {type(dt).__name__}"
            )
        elif dt.tzinfo is None:
            raise TimezoneUnawareError("UserLocalTime", dt)
        else:
            self.dt = dt
        self.tzinfo = dt.tzinfo

    def get_start_of_day(self) -> "UserLocalTime":
        """Midnight of this date, same timezone."""
        return UserLocalTime(
            self.dt.replace(hour=0, minute=0, second=0, microsecond=0)
        )

    def get_dt_for_db(self) -> datetime:
        """Alias for .dt — marks the intent of 'going to the database'."""
        return self.dt

    def __repr__(self):
        return f"UserLocalTime({self.dt!r})"

    def __str__(self):
        return f"UserLocalTime('{self.dt}')"

    def __eq__(self, other):
        if isinstance(other, UserLocalTime):
            return self.dt == other.dt
        return NotImplemented

    def __hash__(self):
        return hash(self.dt)


class SystemTime:
    """
    A datetime in system time (typically UTC).

    Same philosophy as UserLocalTime: thin label, explicit unwrap.
    """

    __slots__ = ("dt",)

    def __init__(self, dt):
        if isinstance(dt, SystemTime):
            self.dt = dt.dt
        elif not isinstance(dt, datetime):
            raise TypeError(
                f"SystemTime expects a datetime, got {type(dt).__name__}"
            )
        else:
            self.dt = dt

    def __repr__(self):
        return f"SystemTime({self.dt!r})"

    def __str__(self):
        return f"SystemTime({self.dt})"

    def __eq__(self, other):
        if isinstance(other, SystemTime):
            return self.dt == other.dt
        return NotImplemented

    def __hash__(self):
        return hash(self.dt)
