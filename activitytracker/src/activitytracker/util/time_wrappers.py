from datetime import datetime

from activitytracker.util.errors import TimezoneUnawareError


class TimeKeeper:
    """
    Exists to resolve painful problems dealing with converting
    what is "the time" to the user into what will be "the time" to the database.

    Problem statement:

    The user is in EST, the database in UTC, some machine off in China in CST when User goes on vacation.
    You have to convert timezones every which way and a plain "datetime" typing
    could mean PST, EST, UTC, CST, JST. How is the developer to know which to use?

    Solution statement:

    Pass around a TimeKeeper that obscures a lot of info, leaving only a useful interface.
    """

    def __init__(self, local_time, local_tz):
        self.local_time = local_time
        self.local_tz = local_tz

    def get_local_time(self):
        pass

    def time_as_utc(self):
        pass

    def get_db_storage_format(self):
        return self.time_as_utc()

    def convert_utc_to_local_time(self, time_as_utc):
        pass


# TODO: "class UtcDatetime"  <- For all dt's that have been converted into utc


class UserLocalTime:
    """
    No longer will datetimes be passed around, leaving
    the developer to wonder if they contain a local time
    or a system-oriented UTC time.

    This class behaves like a datetime while clearly indicating
    that it represents a user's local time.

    The utility happens mostly in the parameter type.
    Now the developer can at a glance see if s/he is dealing with
    the user's timezone or the system's.

    That said: It is OK to unwrap the .dt object once it's into the DAO layer!
    Since Postgres only understands datetime, and the purpose is only to clarify contents.
    """

    def __init__(self, dt):
        if isinstance(dt, UserLocalTime):
            # Handle case where we wrap a UserLocalTime with another UserLocalTime
            self.dt = dt.dt
        else:
            if dt.tzinfo is None:
                raise TimezoneUnawareError("UserLocalTime", dt)
            self.dt = dt
        self.timezone = getattr(self.dt, "tzinfo", None)

    def get_dt_for_db(self):
        return self.dt

    def __getattr__(self, name):
        """Forward attribute access to the underlying datetime object"""
        # This prevents infinite recursion during copying
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")
        return getattr(self.dt, name)

    def __repr__(self):
        return f"UserLocalTime({self.dt!r})"

    def get_time(self):
        """Legacy method for backward compatibility"""
        return self.dt

    def get_start_of_day(self):
        """Get the start of the day for this time"""
        dt = self.dt.replace(hour=0, minute=0, second=0, microsecond=0)
        # This .replace() MUST live here, regardless of the existing util func,
        # to avoid a circular import.
        return UserLocalTime(dt)

    # Optional: Implement other datetime methods directly
    # This allows for direct calling like my_time.strftime()

    def strftime(self, format_string):
        return self.dt.strftime(format_string)

    # To support datetime-like comparison operations
    def __eq__(self, other):
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt == other.dt
        elif isinstance(other, datetime):
            return self.dt == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt < other.dt
        elif isinstance(other, datetime):
            return self.dt < other
        return NotImplemented

    # Support datetime arithmetic
    def __sub__(self, other):
        """Support subtraction between time objects or timedelta objects"""
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt - other.dt
        elif isinstance(other, datetime):
            return self.dt - other
        elif hasattr(other, "days"):  # Check if it's a timedelta-like object
            return UserLocalTime(self.dt - other)
        return NotImplemented

    def __rsub__(self, other):
        """Support subtraction when UserLocalTime is on the right side"""
        if isinstance(other, datetime):
            return other - self.dt
        return NotImplemented

    def __add__(self, timedelta_obj):
        """Add a timedelta to this time, returning a new UserLocalTime"""
        return UserLocalTime(self.dt + timedelta_obj)

    def __radd__(self, timedelta_obj):
        """Support timedelta + UserLocalTime"""
        return self.__add__(timedelta_obj)

    # Support for copying
    def __copy__(self):
        """Support for copy.copy()"""
        return UserLocalTime(self.dt)

    def __deepcopy__(self, memo):
        """Support for copy.deepcopy()"""
        from copy import deepcopy

        return UserLocalTime(deepcopy(self.dt, memo))

    def __gt__(self, other):
        """Support greater than comparison (>)"""
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt > other.dt
        elif isinstance(other, datetime):
            return self.dt > other
        return NotImplemented

    def __le__(self, other):
        """Support less than or equal comparison (<=)"""
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt <= other.dt
        elif isinstance(other, datetime):
            return self.dt <= other
        return NotImplemented

    def __str__(self):
        return str(f"UserLocalTime('{str(self.dt)})'")


# TODO: Implement a .to_system_time() method
# Converted into system time, it should keep track of what it previously was


class SystemTime:
    """
    Represents a datetime in the system's time (typically UTC).
    Behaves like a datetime while clearly indicating its system-time nature.
    """

    def __init__(self, dt):
        if isinstance(dt, SystemTime):
            # Handle case where we wrap a SystemTime with another SystemTime
            self.dt = dt.dt
        else:
            self.dt = dt
        self.timezone = getattr(self.dt, "tzinfo", None)

    def __getattr__(self, name):
        """Forward attribute access to the underlying datetime object"""
        # This prevents infinite recursion during copying
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")
        return getattr(self.dt, name)

    def __str__(self):
        return f"SystemTime({self.dt})"

    def __repr__(self):
        return f"SystemTime({self.dt!r})"

    def get_time(self):
        """Legacy method for backward compatibility"""
        return self.dt

    # Support for copying
    def __copy__(self):
        """Support for copy.copy()"""
        return SystemTime(self.dt)

    def __deepcopy__(self, memo):
        """Support for copy.deepcopy()"""
        from copy import deepcopy

        return SystemTime(deepcopy(self.dt, memo))

    # To support datetime-like comparison operations
    def __eq__(self, other):
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt == other.dt
        elif isinstance(other, datetime):
            return self.dt == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt < other.dt
        elif isinstance(other, datetime):
            return self.dt < other
        return NotImplemented

    # Support datetime arithmetic - same as UserLocalTime
    def __sub__(self, other):
        """Support subtraction between time objects"""
        if isinstance(other, (UserLocalTime, SystemTime)):
            return self.dt - other.dt
        elif isinstance(other, datetime):
            return self.dt - other
        return NotImplemented

    def __rsub__(self, other):
        """Support subtraction when SystemTime is on the right side"""
        if isinstance(other, datetime):
            return other - self.dt
        return NotImplemented

    def __add__(self, timedelta_obj):
        """Add a timedelta to this time, returning a new SystemTime"""
        return SystemTime(self.dt + timedelta_obj)

    def __radd__(self, timedelta_obj):
        """Support timedelta + SystemTime"""
        return self.__add__(timedelta_obj)
