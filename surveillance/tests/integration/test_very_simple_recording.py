import pytest

from datetime import datetime, timedelta

from typing import cast

from surveillance.src.config.definitions import window_push_length
from surveillance.src.object.classes import ProgramSession, ChromeSession
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.models import DailyProgramSummary, ProgramSummaryLog, DailyDomainSummary, DomainSummaryLog
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.time_formatting import get_start_of_day_from_ult
from surveillance.src.util.time_wrappers import UserLocalTime


from ..helper.confirm_chronology import (
    assert_test_data_is_chronological_with_tz,
    get_durations_from_test_data,
)

from ..helper.polling_util import count_full_loops
from ..helper.counting import get_total_in_sec, get_logs_total

from ..data.arbiter_events import test_sessions, times_for_system_clock_as_ult, session1, session2

from ..mocks.mock_clock import MockClock, UserLocalTimeMockClock


@pytest.fixture
def setup_daos(db_session_in_mem):
    
    program_logging_dao = ProgramLoggingDao(db_session_in_mem)
    chrome_logging_dao = ChromeLoggingDao(db_session_in_mem)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, db_session_in_mem)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, db_session_in_mem)
    
    clock = UserLocalTimeMockClock(times_for_system_clock_as_ult)

    
    return {"program_logging": program_logging_dao, "chrome_logging": chrome_logging_dao,
            "program_summary": program_summary_dao, "chrome_summary": chrome_summary_dao
            }
    
def test_simple_round_trip_for_programs(setup_daos):
    selection_for_test = session2
    assert isinstance(selection_for_test, ProgramSession)
    # Enters into KeepAlive
    setup_daos["program_summary"].start_session(selection_for_test)
    # Suppose the session lasts 34 sec
    session_duration = 34
    first_write_time = selection_for_test.start_time.dt
    second_write_time = first_write_time + timedelta(seconds=10)
    third_write_time = first_write_time + timedelta(seconds=20)
    setup_daos["program_summary"].push_window_ahead_ten_sec(selection_for_test)
    setup_daos["program_summary"].push_window_ahead_ten_sec(selection_for_test)
    setup_daos["program_summary"].push_window_ahead_ten_sec(selection_for_test)
    start_of_day = get_start_of_day_from_ult(selection_for_test.start_time)
    setup_daos["program_summary"].add_used_time(selection_for_test, 4, start_of_day)

    # Should now have 34 sec in the db
    entry = setup_daos["program_summary"].read_day(start_of_day)

    entry = entry[0]
    assert isinstance(entry, DailyProgramSummary)
    assert entry.exe_path_as_id == selection_for_test.exe_path
    assert entry.process_name == selection_for_test.process_name
    assert entry.hours_spent == 34 / SECONDS_PER_HOUR



def test_simple_round_trip_for_chrome(setup_daos):
    selection_for_test = session1
    assert isinstance(selection_for_test, ChromeSession)
    # Enters into KeepAlive
    setup_daos["chrome_summary"].start_session(selection_for_test)
    # Suppose the session lasts 38 sec
    session_duration = 38
    first_write_time = selection_for_test.start_time.dt
    second_write_time = first_write_time + timedelta(seconds=10)
    third_write_time = first_write_time + timedelta(seconds=20)
    setup_daos["chrome_summary"].push_window_ahead_ten_sec(selection_for_test)
    setup_daos["chrome_summary"].push_window_ahead_ten_sec(selection_for_test)
    setup_daos["chrome_summary"].push_window_ahead_ten_sec(selection_for_test)
    start_of_day = get_start_of_day_from_ult(selection_for_test.start_time)
    setup_daos["chrome_summary"].add_used_time(selection_for_test, 8, start_of_day)

    # Should now have 38 sec in the db
    entry = setup_daos["chrome_summary"].read_day(start_of_day)

    entry = entry[0]
    assert isinstance(entry, DailyDomainSummary)
    assert entry.domain_name == selection_for_test.domain
    assert entry.hours_spent == 38 / SECONDS_PER_HOUR

def test_simple_logging_activity_for_program(setup_daos):
    """Test does the logging for the above changes"""
    program_logging = setup_daos["program_logging"]
    program_session = session2
    assert isinstance(program_session, ProgramSession)

    # Assume program session is 34 sec, chrome session is 38 sec
    program_duration = 34
    
    print("starting sesssion at ", program_session.start_time)
    program_logging.start_session(program_session)
    program_logging.push_window_ahead_ten_sec(program_session)
    program_logging.push_window_ahead_ten_sec(program_session)
    program_logging.push_window_ahead_ten_sec(program_session)

    program_end_time = program_session.start_time.dt + timedelta(seconds=program_duration)
    program_session = program_session.to_completed(UserLocalTime(program_end_time))
    program_logging.finalize_log(program_session)

    # Now take it all back out
    start_of_day = get_start_of_day_from_ult(program_session.start_time)
    entries = program_logging.read_day_as_sorted(start_of_day)
    
    assert len(entries) == 1
    assert isinstance(entries, dict)
    assert isinstance(entries[program_session.get_name()], list)

    list_of_logs = entries[program_session.get_name()]

    assert list_of_logs[0].process_name == program_session.process_name
    assert list_of_logs[0].duration_in_sec == program_duration

def test_simple_logging_activity_for_chrome(setup_daos):
    """Test does the logging for the above changes"""
    chrome_logging = setup_daos["chrome_logging"]
    chrome_session = session1
    assert isinstance(chrome_session, ChromeSession)

    # Assume program session is 34 sec, chrome session is 38 sec
    chrome_duration = 38
    print("starting sesssion at ", chrome_session.start_time)
    
    chrome_logging.start_session(chrome_session)
    chrome_logging.push_window_ahead_ten_sec(chrome_session)
    chrome_logging.push_window_ahead_ten_sec(chrome_session)
    chrome_logging.push_window_ahead_ten_sec(chrome_session)

    chrome_end_time = chrome_session.start_time.dt + timedelta(seconds=chrome_duration)
    chrome_session = chrome_session.to_completed(UserLocalTime(chrome_end_time))
    chrome_logging.finalize_log(chrome_session)

    # Now take it all back out
    start_of_day = get_start_of_day_from_ult(chrome_session.start_time)
    entries = chrome_logging.read_day_as_sorted(start_of_day)

    assert len(entries) == 1
    assert isinstance(entries, dict)
    assert isinstance(entries[chrome_session.get_name()], list)

    list_of_logs = entries[chrome_session.get_name()]

    assert list_of_logs[0].domain_name == chrome_session.domain
    assert list_of_logs[0].duration_in_sec == chrome_duration