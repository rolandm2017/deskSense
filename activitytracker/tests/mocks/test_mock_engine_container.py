from unittest.mock import Mock

import asyncio

import pytz
import time
from datetime import datetime

from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.arbiter.session_polling import (
    KeepAliveEngine,
    ThreadedEngineContainer,
)
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.time_wrappers import UserLocalTime

from .mock_engine_container import MockEngineContainer

timezone_for_test = "Asia/Tokyo"  # UTC+9

tokyo_tz = pytz.timezone(timezone_for_test)


def test_mock_engine_container(mock_regular_session_maker, mock_async_session):
    """
    Notes for debugging:

    - Run 1's outcome can only be tested after run 2 is started.

    - You must reset the mocks after run 1's outcome is tested, but before run 2 activates.


    """

    p_logging_dao = ProgramLoggingDao(mock_regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(mock_regular_session_maker)

    p_summary_dao = ProgramSummaryDao(p_logging_dao, mock_regular_session_maker)
    chrome_sum_dao = ChromeSummaryDao(chrome_logging_dao, mock_regular_session_maker)

    clock = UserFacingClock()

    video_logging_dao = VideoLoggingDao(mock_regular_session_maker)
    video_summary_dao = VideoSummaryDao(video_logging_dao, mock_regular_session_maker)

    mystery_dao = MysteryMediaDao(mock_regular_session_maker)

    recorder = ActivityRecorder(
        p_logging_dao,
        chrome_logging_dao,
        video_logging_dao,
        p_summary_dao,
        chrome_sum_dao,
        video_summary_dao,
        mystery_dao,
    )

    window_push_mock = Mock()
    add_partial_window_mock = Mock()

    recorder.add_ten_sec_to_end_time = window_push_mock
    recorder.add_partial_window = add_partial_window_mock

    t1 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 1, 1, 1)))
    t2 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 2, 2, 2)))
    t3 = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 24, 3, 3, 3)))

    session1 = ProgramSession("path/to/bar.exe", "bar.exe", "", "", t1)
    session2 = ChromeSession("foo.com", "Foo Dot Com", t2)

    pulse_interval = 0.1

    first_engine = KeepAliveEngine(session1, recorder)
    first_engine.conclude_engine = Mock(wraps=first_engine.conclude_engine)

    duration_in_sec_1 = 33
    partial1 = 3

    duration_in_sec_2 = 56
    partial2 = 6

    duration_in_sec_3 = 7
    partial3 = 7

    run_durations = [duration_in_sec_1, duration_in_sec_2, duration_in_sec_3]

    # Time.sleep isn't used
    engine_container = MockEngineContainer(run_durations, pulse_interval)

    engine_container.add_first_engine(first_engine)

    engine_container.start()

    # An arbiter loop passes, and then:

    # assert window push happened 3x
    assert window_push_mock.call_count == 3

    window_push_mock.reset_mock()
    add_partial_window_mock.reset_mock()

    # --
    # -- Run #2
    # --

    second_engine = KeepAliveEngine(session2, recorder)
    second_engine.conclude_engine = Mock(wraps=second_engine.conclude_engine)

    engine_container.replace_engine(second_engine)

    # assert add_partial_window happened 1x for 7 sec,
    # because replace_engine() causes conclude_engine().
    # So you can't test the outcome of run 1 until you start run 2.
    assert first_engine.conclude_engine.call_count == 1
    assert add_partial_window_mock.call_count == 1
    call_args = add_partial_window_mock.call_args[0]  # Get positional args
    assert call_args[0] == partial1  # First arg
    assert call_args[1] == session1  # Second arg
    assert call_args[1].get_name() == session1.get_name()

    # An arbiter loop passes, and then:

    assert window_push_mock.call_count == 5  # (50 / 10 = 5)
    # assert add_partial_window happened 1x for 7 sec
    assert add_partial_window_mock.call_count == 1

    window_push_mock.reset_mock()
    add_partial_window_mock.reset_mock()

    # --
    # -- Run #3
    # --

    session3 = ChromeSession("test.com", "Test your code", t3)

    third_engine = KeepAliveEngine(session3, recorder)
    third_engine.conclude_engine = Mock(wraps=third_engine.conclude_engine)

    engine_container.replace_engine(third_engine)

    first_arg = add_partial_window_mock.call_args_list[0][0][0]
    second_arg = add_partial_window_mock.call_args_list[0][0][1]
    assert isinstance(first_arg, int)
    assert first_arg == partial2
    assert isinstance(second_arg, ChromeSession)
    assert second_arg.get_name() == session2.get_name()

    window_push_mock.reset_mock()
    add_partial_window_mock.reset_mock()

    # An arbiter loop passes, and then:

    engine_container.stop()

    window_push_mock.assert_not_called()

    first_arg = add_partial_window_mock.call_args_list[0][0][0]
    second_arg = add_partial_window_mock.call_args_list[0][0][1]
    assert isinstance(first_arg, int)
    assert first_arg == partial3
    assert isinstance(second_arg, ChromeSession)
    assert second_arg.get_name() == session3.get_name()
