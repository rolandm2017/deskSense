from functools import wraps

def validate_session(func):
    @wraps(func)
    def wrapper(self, session, *args, **kwargs):
        if session.duration is None:
            raise ValueError("Session duration was None")
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")
        return func(self, session, *args, **kwargs)
    return wrapper
