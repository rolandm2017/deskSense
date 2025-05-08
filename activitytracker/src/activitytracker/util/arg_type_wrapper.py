from functools import wraps

from activitytracker.tz_handling.time_formatting import convert_to_timezone

from activitytracker.util.time_wrappers import UserLocalTime


def is_really_ult(func):
    @wraps(func)
    def wrapper(self, ult, *args, **kwargs):
        if not isinstance(ult, UserLocalTime):
            raise ValueError(f"Expected a UserLocalTime and it was {type(ult)}")
        return func(self, ult, *args, **kwargs)

    return wrapper


def validate_start_end_and_duration(func):
    @wraps(func)
    def wrapper(self, session, *args, **kwargs):
        if session.duration is None:
            raise ValueError("Session duration was None")
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")
        return func(self, session, *args, **kwargs)

    return wrapper


def validate_start_and_end_times(func):
    @wraps(func)
    def wrapper(self, session, *args, **kwargs):
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")
        return func(self, session, *args, **kwargs)

    return wrapper


def validate_session(func):
    @wraps(func)
    def wrapper(self, session, *args, **kwargs):
        if session.duration is None:
            raise ValueError("Session duration was None")
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")
        return func(self, session, *args, **kwargs)

    return wrapper


def guarantee_start_time(func):
    @wraps(func)
    def wrapper(self, session, *args, **kwargs):
        if session.start_time is None:
            raise ValueError("Start time was None")
        return func(self, session, *args, **kwargs)

    return wrapper
