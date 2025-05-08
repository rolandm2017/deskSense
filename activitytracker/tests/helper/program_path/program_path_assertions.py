from activitytracker.object.classes import ProgramSession


def assert_session_was_in_order(actual: ProgramSession, i, test_events):
    """The first one"""
    expected = test_events[i]
    # print("Loop: ", i)
    # print("Expected:", expected.start_time)
    # print("Actual:", actual.start_time)
    assert actual.exe_path == expected.exe_path
    assert actual.process_name == expected.process_name
    assert actual.window_title == expected.window_title
    assert actual.detail == expected.detail
    assert actual.start_time == expected.start_time


def assert_add_partial_window_happened_as_expected(event_count, recorder_spies, test_events):
    """
    Deduct duration might happen 3x b/c of the final val staying in the Arbiter.
    """
    # This func does not use assert_all_spy_args_were_sessions because
    # the arg order is reversed here, i.e. 0th arg is an int
    one_left_in_arb = 1
    total_loops = event_count - one_left_in_arb
    for i in range(0, total_loops):
        some_duration = recorder_spies["add_partial_window_spy"].call_args_list[i][0][0]
        assert isinstance(some_duration, int)

        some_session = recorder_spies["add_partial_window_spy"].call_args_list[i][0][1]
        assert isinstance(some_session, ProgramSession)
        assert_session_was_in_order(some_session, i, test_events)

    call_count = len(recorder_spies["add_partial_window_spy"].call_args_list)
    assert call_count == total_loops, f"Expected exactly {total_loops} calls"
