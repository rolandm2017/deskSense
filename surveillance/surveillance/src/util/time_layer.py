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


class UserLocalTime:
    """
    No longer will datetimes be passed around, leaving
    the developer to wonder if they contain a local time
    or a system-oriented UTC time.
    """

    def __init__(self):
        pass


class SystemTime:
    """
    Represents a time that is timezone-agnostic,
    i.e. has a UTC time.
    """

    def __init__(self):
        pass
