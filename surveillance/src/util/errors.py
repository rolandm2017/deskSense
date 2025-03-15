class SuspiciousDurationError(ValueError):
    """Raised when session duration is unexpectedly large."""

    def __init__(self, error_type: str, message: str = ""):
        self.error_type = error_type
        self.message = message or f"Suspicious duration detected: {error_type}"
        super().__init__(self.message)


class TimezoneUnawareError(ValueError):
    """Raised when a datetime object is missing timezone info."""

    def __init__(self, variable_name: str):
        super().__init__(
            f"Timezone-unaware datetime detected: {variable_name}")


class MismatchedTimezonesError(ValueError):
    """Raised when two datetime objects have different timezones."""

    def __init__(self):
        super().__init__("Mismatched timezones detected.")
