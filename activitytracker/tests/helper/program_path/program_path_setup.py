from unittest.mock import Mock

from datetime import datetime, timedelta

from activitytracker.db.models import DailyProgramSummary, ProgramSummaryLog
from activitytracker.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.const import SECONDS_PER_HOUR, ten_sec_as_pct_of_hour
from activitytracker.util.time_wrappers import UserLocalTime

from ...data.program_session_path import session1, session2, session3, session4

# --
# -- Existing entries mocks
# --


def make_preexisting_summary(session, id_for_session, summary_starting_hours):
    return DailyProgramSummary(
        id=id_for_session,
        exe_path_as_id=session.exe_path,
        program_name=session.window_title,
        hours_spent=summary_starting_hours,
        gathering_date=get_start_of_day_from_datetime(session.start_time),
        gathering_date_local=get_start_of_day_from_datetime(session.start_time).replace(
            tzinfo=None
        ),
    )


def group_of_preexisting_summaries(made_up_pids, summary_starting_hours):
    yield make_preexisting_summary(session1, made_up_pids[0], summary_starting_hours)
    yield make_preexisting_summary(session2, made_up_pids[1], summary_starting_hours)
    yield make_preexisting_summary(session3, made_up_pids[2], summary_starting_hours)
    yield make_preexisting_summary(session4, made_up_pids[3], summary_starting_hours)
    # return [s1,s2,s3,s4]


def make_preexisting_log(session, id_for_log):
    """Makes the log file found in the db from a prev. session"""
    sixty_sec = 60
    # Note that the test data is from  "2025-03-22 16:16:17.480951-07:00" ish. 03-22.
    very_early_morning = datetime(2025, 3, 22, 5, 35, 50)
    return ProgramSummaryLog(
        id=id_for_log,
        exe_path_as_id=session.process_name,
        process_name=session.process_name,
        program_name=session.window_title,
        # Assumes (10 - n) sec will be deducted later
        hours_spent=sixty_sec / SECONDS_PER_HOUR,
        start_time=very_early_morning,
        end_time=very_early_morning + timedelta(minutes=5),
        duration_in_sec=60.0,
        gathering_date=get_start_of_day_from_datetime(very_early_morning),
        gathering_date_local=get_start_of_day_from_datetime(very_early_morning).replace(
            tzinfo=None
        ),
        created_at=very_early_morning,
    )


def group_of_preexisting_logs(made_up_pids):
    yield make_preexisting_log(session1, made_up_pids[0])
    yield make_preexisting_log(session2, made_up_pids[1])
    yield make_preexisting_log(session3, made_up_pids[2])
    yield make_preexisting_log(session4, made_up_pids[3])


# --
# -- Fresh entries content
# --


def make_log_from_session(session):
    """Makes the log file created in the DAO"""
    base_start_time_as_utc = convert_to_utc(session.start_time.get_dt_for_db())
    start_of_day = get_start_of_day_from_datetime(session.start_time.get_dt_for_db())
    if isinstance(start_of_day, UserLocalTime):
        raise ValueError("Expected datetime")
    start_of_day_as_utc = convert_to_utc(start_of_day)
    start_window_end = base_start_time_as_utc + timedelta(seconds=10)
    return ProgramSummaryLog(
        exe_path_as_id=session.exe_path,
        process_name=session.process_name,
        program_name=session.window_title,
        # Assumes (10 - n) sec will be deducted later
        hours_spent=ten_sec_as_pct_of_hour,
        start_time=base_start_time_as_utc,  # FIXME: start_time_local is missing
        end_time=start_window_end,  # FIXME: _local mia
        duration_in_sec=0,
        gathering_date=start_of_day_as_utc,
        gathering_date_local=start_of_day_as_utc.replace(tzinfo=None),
        created_at=base_start_time_as_utc,
    )


def make_mock_db_rows_for_test_data():
    """
    The test "just made" these logs during the test. They're mocks but
    if it really did run with the db attached, the find_session method
    would indeed find these logs sitting there
    """
    # FIXME: you MUST account for find_session() being hit more than four times.
    # FIXME: push_window_ahead_ten_sec hits it, finalize_log hits it.
    # for now cook it by hand
    yield make_log_from_session(session1)
    yield make_log_from_session(session2)
    yield make_log_from_session(session3)
    yield make_log_from_session(session4)


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
