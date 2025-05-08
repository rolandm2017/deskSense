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


def setup_summary_dao_spies(p_summary_dao):
    summary_start_session_spy = Mock(side_effect=p_summary_dao.start_session)
    p_summary_dao.start_session = summary_start_session_spy

    summary_add_new_item_spy = Mock()
    p_summary_dao.add_new_item = summary_add_new_item_spy

    push_window_ahead_ten_sec_spy = Mock(side_effect=p_summary_dao.push_window_ahead_ten_sec)
    p_summary_dao.push_window_ahead_ten_sec = push_window_ahead_ten_sec_spy

    make_find_all_from_day_query_spy = Mock(
        side_effect=p_summary_dao.create_find_all_from_day_query
    )
    p_summary_dao.create_find_all_from_day_query = make_find_all_from_day_query_spy

    execute_window_push_spy = Mock()
    p_summary_dao.execute_window_push = execute_window_push_spy

    do_addition_spy = Mock()
    p_summary_dao.do_addition = do_addition_spy

    return p_summary_dao, {
        "summary_start_session_spy": summary_start_session_spy,
        "summary_add_new_item_spy": summary_add_new_item_spy,
        "push_window_ahead_ten_sec_spy": push_window_ahead_ten_sec_spy,
        "make_find_all_from_day_query_spy": make_find_all_from_day_query_spy,
        "execute_window_push_spy": execute_window_push_spy,
        "do_addition_spy": do_addition_spy,
    }
