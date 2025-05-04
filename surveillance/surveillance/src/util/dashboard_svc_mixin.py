from datetime import timedelta, datetime

from surveillance.src.util.time_wrappers import UserLocalTime


class WeekCalculationMixin:
    """
    A mixin that provides week calculation functionality.
    Can be used by any service that needs to determine the start of a week.
    """

    def prepare_start_of_week(self, today: UserLocalTime):
        """
        Calculate the Sunday that starts the week containing the given date.

        Args:
            today: A UserLocalTime object representing the reference date.

        Returns:
            UserLocalTime: A UserLocalTime object representing the Sunday that starts the week.
        """
        is_sunday = today.weekday() == 6
        if is_sunday:
            # If the week_of is a sunday, start from there.
            sunday_that_starts_the_week = today
        else:
            # If the week_of is not a sunday,
            # go back in time to the most recent sunday,
            # and start from there. This is error handling
            offset = 1
            days_per_week = 7
            days_since_sunday = (today.weekday() + offset) % days_per_week
            sunday_that_starts_the_week = UserLocalTime(today.dt -
                                                        timedelta(days=days_since_sunday))
        return sunday_that_starts_the_week
