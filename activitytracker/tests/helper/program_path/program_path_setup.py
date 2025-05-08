from unittest.mock import Mock


def setup_recorder_spies(recorder):
    on_new_session_spy = Mock(side_effect=recorder.on_new_session)
    recorder.on_new_session = on_new_session_spy

    add_ten_sec_to_end_time_spy = Mock(side_effect=recorder.add_ten_sec_to_end_time)
    recorder.add_ten_sec_to_end_time = add_ten_sec_to_end_time_spy

    on_state_changed_spy = Mock(side_effect=recorder.on_state_changed)
    recorder.on_state_changed = on_state_changed_spy

    add_partial_window_spy = Mock(side_effect=recorder.add_partial_window)
    recorder.add_partial_window = add_partial_window_spy

    return recorder, {
        "on_new_session_spy": on_new_session_spy,
        "add_ten_sec_to_end_time_spy": add_ten_sec_to_end_time_spy,
        "on_state_changed_spy": on_state_changed_spy,
        "add_partial_window_spy": add_partial_window_spy,
    }
