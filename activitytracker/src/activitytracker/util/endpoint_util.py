from datetime import timezone

from activitytracker.util.errors import MustHaveUtcTzInfoError


def field_has_utc_tzinfo_else_throw(start_time_field):
    utc_dt = start_time_field.tzinfo == timezone.utc
    if not utc_dt:
        raise MustHaveUtcTzInfoError()
