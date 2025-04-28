from unittest.mock import Mock

import asyncio

import time
from datetime import datetime
import pytz


from surveillance.src.arbiter.session_heartbeat import ThreadedEngineContainer
from surveillance.src.arbiter.session_heartbeat import KeepAliveEngine

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.object.classes import ProgramSession, ChromeSession
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.clock import UserFacingClock

from .mock_clock import UserLocalTimeMockClock
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
    deduct_duration_mock = Mock()

    recorder.add_ten_sec_to_end_time = window_push_mock
    recorder.deduct_duration = deduct_duration_mock

    t1 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 1, 1, 1)))
    t2 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 2, 2, 2)))

    session1 = ProgramSession("path/to/bar.exe", "bar.exe")
    session2 = ChromeSession("foo.com", "Experience Foo", t2)
    
    pulse_interval = 0.1
 
    start_of_loop = asyncio.new_event_loop()
    an_engine = KeepAliveEngine(session1, recorder)

    # Time.sleep isn't used
    engine_container = MockEngineContainer(an_engine, pulse_interval)

    duration_in_sec = 33
    remainder = 40 - 33
    engine_container.start(duration_in_sec)

    # An arbiter loop passes, and then:

    engine_container.stop()

    # assert window push happened 3x
    assert window_push_mock.call_count == 3
    # assert deduct_duration happened 1x for 7 sec
    assert deduct_duration_mock.call_count == 1
    deduct_duration_mock.assert_called_once_with(remainder, session1)

    window_push_mock.reset_mock()
    deduct_duration_mock.reset_mock()

    # --
    # -- Run #2
    # --

    duration_in_sec = 56
    remainder = 60 - 56

    an_engine = KeepAliveEngine(session2, recorder)

    engine_container = MockEngineContainer(an_engine, pulse_interval)

    engine_container.start(duration_in_sec)

    # An arbiter loop passes, and then:

    engine_container.stop()

    assert window_push_mock.call_count == 5  # (50 / 10 = 5)
    # assert deduct_duration happened 1x for 7 sec
    assert deduct_duration_mock.call_count == 1
    deduct_duration_mock.assert_called_once_with(remainder, session2)

    window_push_mock.reset_mock()
    deduct_duration_mock.reset_mock()

    # --
    # -- Run #3
    # --

    duration_in_sec = 7
    remainder = 10 - 7

    session3 = ProgramSession()

    an_engine = KeepAliveEngine(session3, recorder)

    engine_container = MockEngineContainer(an_engine, pulse_interval)

    engine_container.start(duration_in_sec)

    # An arbiter loop passes, and then:

    engine_container.stop()

    window_push_mock.assert_not_called()
    assert deduct_duration_mock.call_count == 1
    deduct_duration_mock.assert_called_once_with(remainder, session3)