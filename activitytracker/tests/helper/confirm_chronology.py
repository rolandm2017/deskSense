from datetime import datetime, timedelta

from activitytracker.util.time_wrappers import UserLocalTime


def assert_start_times_are_chronological(test_events):
    chronological_sessions = sorted(test_events, key=lambda event: event.start_time.dt)
    for i in range(0, len(test_events)):
        assert (
            chronological_sessions[i].start_time == test_events[i].start_time
        ), "Something was not chronological"


def assert_all_start_times_precede_end_times(test_events):
    for i in range(0, len(test_events)):
        if test_events[i].end_time:
            assert test_events[i].start_time < test_events[i].end_time


def assert_test_data_is_chronological_with_tz(test_events):
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""
    # Validate your dummy test data
    for i in range(0, len(test_events)):
        assert isinstance(test_events[i].start_time, UserLocalTime)
        assert isinstance(test_events[i].start_time.dt, datetime)
        assert test_events[i].start_time.dt.tzinfo is not None

        if i == len(test_events) - 1:
            break  # There is no next val to link with
        assert (
            test_events[i].start_time < test_events[i + 1].start_time
        ), "Events must be chronological"

    # Return the data to the test
    return test_events


def get_durations_from_test_data(test_events):
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""
    durations_for_sessions = []
    for i in range(0, len(test_events)):
        if i == len(test_events) - 1:
            break  # nothing to link up with

        elapsed_between_sessions: timedelta = (
            test_events[i + 1].start_time.dt - test_events[i].start_time.dt
        )
        seconds = elapsed_between_sessions.total_seconds()
        durations_for_sessions.append(seconds)

    return durations_for_sessions
