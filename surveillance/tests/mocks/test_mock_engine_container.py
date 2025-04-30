from unittest.mock import Mock

import asyncio

import time
from datetime import datetime
import pytz


from surveillance.src.arbiter.session_polling import ThreadedEngineContainer
from surveillance.src.arbiter.session_polling import KeepAliveEngine

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.object.classes import ProgramSession, ChromeSession
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.clock import UserFacingClock

from .mock_engine_container import MockEngineContainer

timezone_for_test = "Asia/Tokyo"  #  UTC+9

tokyo_tz = pytz.timezone(timezone_for_test)



def test_engine_container(mock_regular_session_maker, mock_async_session):

    p_logging_dao = ProgramLoggingDao(mock_regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(mock_regular_session_maker)

    p_summary_dao = ProgramSummaryDao(
        p_logging_dao, mock_regular_session_maker, mock_async_session)
    chrome_sum_dao = ChromeSummaryDao(
        chrome_logging_dao, mock_regular_session_maker, mock_async_session)


    clock = UserFacingClock()

    recorder = ActivityRecorder(clock,  p_logging_dao, chrome_logging_dao, p_summary_dao, chrome_sum_dao)
    
    window_push_mock = Mock()
    add_partial_window_mock = Mock()

    recorder.add_ten_sec_to_end_time = window_push_mock
    recorder.add_partial_window = add_partial_window_mock

    t1 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 1, 1, 1)))
    t2 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 2, 2, 2)))

    session1 = ProgramSession("path/to/bar.exe", "bar.exe")
    session2 = ChromeSession("foo.com", "Experience Foo", t2)
    
    pulse_interval = 0.1
 
    an_engine = KeepAliveEngine(session1, recorder)

    duration_in_sec_1 = 33
    partial1 = 3

    duration_in_sec_2 = 56
    partial2 = 6

    duration_in_sec_3 = 7
    partial3 = 7

    run_durations = [duration_in_sec_1, duration_in_sec_2, duration_in_sec_3]

    # Time.sleep isn't used
    engine_container = MockEngineContainer(run_durations, pulse_interval)

    engine_container.add_first_engine(an_engine)

    engine_container.start()

    # An arbiter loop passes, and then:

    engine_container.stop()

    # assert window push happened 3x
    assert window_push_mock.call_count == 3
    # assert add_partial_window happened 1x for 7 sec
    assert add_partial_window_mock.call_count == 1
    add_partial_window_mock.assert_called_once_with(partial1, session1)

    window_push_mock.reset_mock()
    add_partial_window_mock.reset_mock()

    # --
    # -- Run #2
    # --

    an_engine = KeepAliveEngine(session2, recorder)
    engine_container.replace_engine(an_engine)

    engine_container.start()

    # An arbiter loop passes, and then:

    engine_container.stop()

    assert window_push_mock.call_count == 5  # (50 / 10 = 5)
    # assert add_partial_window happened 1x for 7 sec
    assert add_partial_window_mock.call_count == 1

    first_arg = add_partial_window_mock.call_args_list[0][0][0]
    second_arg = add_partial_window_mock.call_args_list[0][0][1]
    assert isinstance(first_arg, int)
    assert first_arg == partial2
    assert isinstance(second_arg, ChromeSession)
    
    add_partial_window_mock.assert_called_once_with(partial2, session2)

    window_push_mock.reset_mock()
    add_partial_window_mock.reset_mock()

    # --
    # -- Run #3
    # --


    session3 = ProgramSession()

    an_engine = KeepAliveEngine(session3, recorder)
    engine_container.replace_engine(an_engine)

    engine_container.start()

    # An arbiter loop passes, and then:

    engine_container.stop()

    window_push_mock.assert_not_called()
    assert add_partial_window_mock.call_count == 1
    add_partial_window_mock.assert_called_once_with(partial3, session3)
