import traceback


class SuspiciousDurationError(ValueError):
    """Raised when session duration is unexpectedly large."""

    def __init__(self, error_type: str, message: str = ""):
        self.error_type = error_type
        self.message = message or f"Suspicious duration detected: {error_type}"
        super().__init__(self.message)


class TimezoneUnawareError(ValueError):
    """Raised when a datetime object is missing timezone info. tzinfo=None -> Here"""

    def __init__(self, source: str, dt):
        super().__init__(
            f"Timezone-unaware datetime detected: {source} with dt {str(dt)}")


class MismatchedTimezonesError(ValueError):
    """Raised when two datetime objects have different timezones."""

    def __init__(self):
        super().__init__("Mismatched timezones detected.")


class ImpossibleToGetHereError(ValueError):
    """For DAO paths that ought to be unreachable if other code worked"""

    def __init__(self, message, *args):
        super().__init__(message, *args)


class WayTooLongWaitError(ValueError):
    """For a DAO queue flush value that would make the tasks hang open for ages"""

    def __init__(self, time, *args):
        message = f"Sleeping the code for {time} seconds is way too long"
        super().__init__(message, *args)


class NegativeTimeError(ValueError):
    """
    For when the summary DAO claims a negative amount of time 
    was spent using a program or website
    """

    def __init__(self, activity, time, *args):
        message = f"The DAO claims {activity} had {time} seconds spent on it"
        super().__init__(message, *args)

class MissingEngineError(ValueError):
    """
    For when the summary DAO claims a negative amount of time 
    was spent using a program or website
    """

    def __init__(self, *args):
        message = f"The KeepAliveEngine was missing"
        super().__init__(message, *args)

class SessionClosedError(Exception):
    """Raised when operations are attempted on a closed session."""
    pass