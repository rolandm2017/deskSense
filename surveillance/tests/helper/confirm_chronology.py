from datetime import datetime, timedelta

from surveillance.src.util.time_wrappers import UserLocalTime

def assert_test_data_is_chronological_with_tz(test_events):
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""
    # Validate your dummy test data
    for i in range(0, len(test_events)):
        assert isinstance(test_events[i].start_time, UserLocalTime)
        assert isinstance(test_events[i].start_time.dt, datetime)
        assert test_events[i].start_time.dt.tzinfo is not None

        if i == len(test_events) - 1:
            break  # There is no next val to link with
        assert test_events[i].start_time < test_events[i + 1].start_time, "Events must be chronological"
    
    # Return the data to the test
    return test_events

def get_durations_from_test_data(test_events):
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""
    durations_for_sessions = []
    for i in range(0, len(test_events)):
        if i == len(test_events) - 1:
            break  # nothing to link up with

        elapsed_between_sessions: timedelta = test_events[i + 1].start_time.dt - test_events[i].start_time.dt
        seconds = elapsed_between_sessions.total_seconds()
        durations_for_sessions.append(seconds)
    
    return durations_for_sessions