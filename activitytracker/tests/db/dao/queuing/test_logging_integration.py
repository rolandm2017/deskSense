"""
Verifies the following methods work as intended:
start_session

find_session
push_window_ahead_ten_sec
finalize_log
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from sqlalchemy.sql.selectable import Select


from sqlalchemy import text

import pytz
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone


from activitytracker.db.models import DomainSummaryLog, ProgramSummaryLog, Base


from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from activitytracker.object.classes import (
    CompletedProgramSession,
    CompletedChromeSession,
    ProgramSession,
    ChromeSession,
)

from activitytracker.tz_handling.time_formatting import convert_to_utc
from activitytracker.util.errors import ImpossibleToGetHereError
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.time_wrappers import UserLocalTime


timezone_for_test_data = ZoneInfo("Asia/Tokyo")

tokyo_tz = pytz.timezone("Asia/Tokyo")

now_tokyo = datetime.now(pytz.UTC).astimezone(tokyo_tz)


def test_round_trip(regular_session_maker):
    """
    Start session, find session to do window push, finalize end time.
    """

    program_logging_dao = ProgramLoggingDao(regular_session_maker)

    start_time = UserLocalTime(
        datetime(2025, 2, 1, 1, 0, 1, 2, tzinfo=timezone_for_test_data)
    )
    end_time = UserLocalTime(datetime(2025, 2, 1, 1, 1, 2, 3, tzinfo=timezone_for_test_data))

    expected_duration = (end_time.dt - start_time.dt).total_seconds()

    expected_start_time_in_utc = convert_to_utc(start_time.dt)
    expected_end_time_in_utc = convert_to_utc(end_time.dt)

    slightly_after_session = UserLocalTime(
        datetime(2025, 2, 1, 1, 44, 2, 3, tzinfo=timezone_for_test_data)
    )

    test_program_session = ProgramSession(
        "Ventrilo", "The Programmer's Hangout", start_time=start_time, productive=False
    )

    # -- spies

    start_session_spy = Mock(side_effect=program_logging_dao.start_session)
    program_logging_dao.start_session = start_session_spy

    find_session_spy = Mock(side_effect=program_logging_dao.find_session)
    program_logging_dao.find_session = find_session_spy

    push_window_spy = Mock(side_effect=program_logging_dao.push_window_ahead_ten_sec)
    program_logging_dao.push_window_ahead_ten_sec = push_window_spy

    finalize_log_spy = Mock(side_effect=program_logging_dao.finalize_log)
    program_logging_dao.finalize_log = finalize_log_spy

    # -- end of spies section
    try:
        program_logging_dao.start_session(test_program_session)

        # find session called under the hood
        program_logging_dao.push_window_ahead_ten_sec(test_program_session)

        completed = test_program_session.to_completed(end_time)

        program_logging_dao.finalize_log(completed)

        # --
        # -- assert
        # --

        start_session_spy.assert_called_once()
        assert find_session_spy.call_count == 2
        push_window_spy.assert_called_once()
        finalize_log_spy.assert_called_once()

        # Now get it back out for asserting
        logs_arr = program_logging_dao.read_last_24_hrs(slightly_after_session)

        # all_vvv = program_logging_dao.read_all()
        # for k in all_vvv:
        #     print(k)

        assert len(logs_arr) == 1

        log = logs_arr[0]

        assert isinstance(log, ProgramSummaryLog)

        duration_from_start_end = (log.end_time - log.start_time).total_seconds()

        print(duration_from_start_end, "123ru")
        print("expected duration in sec:", expected_duration)
        assert log.duration_in_sec == expected_duration
        assert log.start_time == expected_start_time_in_utc  # but as utc
        assert log.end_time == expected_end_time_in_utc
    finally:
        with regular_session_maker() as session:
            session.execute(text("TRUNCATE program_logs RESTART IDENTITY CASCADE"))
            session.commit()
            print("Super truncated tables")
