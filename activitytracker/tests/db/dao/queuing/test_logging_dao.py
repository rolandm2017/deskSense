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


@pytest.fixture
def mock_session_data():
    test_program_session = ProgramSession(
        "Ventrilo",
        "The Programmer's Hangout",
        start_time=UserLocalTime(
            datetime(2025, 2, 1, 1, 0, 4, 0, tzinfo=timezone_for_test_data)
        ),
        productive=False,
    )

    test_chrome_session = ChromeSession(
        "chatgpt.com",
        "gpt Chat Repository",
        UserLocalTime(datetime(2025, 2, 1, 1, 0, 5, 0, tzinfo=timezone_for_test_data)),
        productive=True,
    )

    return test_program_session, test_chrome_session


@pytest_asyncio.fixture
async def prepare_daos(mock_regular_session_maker, mock_async_session):
    program_dao = ProgramLoggingDao(mock_regular_session_maker)
    chrome_dao = ChromeLoggingDao(mock_regular_session_maker)

    yield program_dao, chrome_dao

    # await program_dao.cleanup()
    # await chrome_dao.cleanup()


@pytest.mark.asyncio
async def test_start_session(prepare_daos, mock_session_data):
    """Test that start_session calls queue_item correctly"""
    # Arrange
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos

    # Act
    program_dao.start_session(program_session)
    chrome_dao.start_session(chrome_session)

    # Assert
    # TODO: Find a way to assert here!
    assert 1 == 1  # TEMP


def test_find_session(prepare_daos, mock_session_data):
    """Test find_session with direct database inserts"""
    # ### Arrange
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos

    pr_execute_and_read_one_mock = Mock()
    ch_execute_and_read_one_mock = Mock()
    program_dao.execute_and_read_one_or_none = pr_execute_and_read_one_mock
    chrome_dao.execute_and_read_one_or_none = ch_execute_and_read_one_mock

    pr_select_where_time_equals_spy = Mock(side_effect=program_dao.select_where_time_equals)
    ch_select_where_time_equals_spy = Mock(side_effect=chrome_dao.select_where_time_equals)
    program_dao.select_where_time_equals = pr_select_where_time_equals_spy
    chrome_dao.select_where_time_equals = ch_select_where_time_equals_spy

    pr_time_as_utc = convert_to_utc(program_session.start_time)
    ch_time_as_utc = convert_to_utc(chrome_session.start_time)

    # ### Act
    _ = program_dao.find_session(program_session)
    _ = chrome_dao.find_session(chrome_session)

    pr_select_where_time_equals_spy.assert_called_with(pr_time_as_utc)
    ch_select_where_time_equals_spy.assert_called_with(ch_time_as_utc)

    args, _ = pr_execute_and_read_one_mock.call_args

    assert isinstance(args[0], Select)

    args, _ = ch_execute_and_read_one_mock.call_args

    assert isinstance(args[0], Select)


def test_push_window_ahead(prepare_daos):
    """Test assumes there is an existing session, which the test can 'push the window forward' for."""
    program_dao, chrome_dao = prepare_daos
    # chrome_dao = ChromeLoggingDao(plain_asm)

    program_update_item_spy = Mock()
    program_dao.update_item = program_update_item_spy

    chrome_update_item_spy = Mock()
    chrome_dao.update_item = chrome_update_item_spy

    start_val_for_test = 33

    program_find_session_mock = Mock()
    pretend_pr_log = ProgramSummaryLog(
        program_name="VSCode",
        hours_spent=120 / SECONDS_PER_HOUR,
        start_time=datetime(2025, 4, 19, 9, 0, 0, tzinfo=tokyo_tz),
        end_time=datetime(2025, 4, 19, 17, 0, start_val_for_test, tzinfo=tokyo_tz),
        duration_in_sec=8.0,
        created_at=datetime.now(tokyo_tz),
        gathering_date=datetime(2025, 4, 19, tzinfo=tokyo_tz),
    )
    program_find_session_mock.return_value = pretend_pr_log
    program_dao.find_session = program_find_session_mock

    chrome_find_session_mock = Mock()
    pretend_domain_log = DomainSummaryLog(
        domain_name="example.com",
        hours_spent=4.5,
        start_time=datetime(2025, 4, 20, 10, 0, tzinfo=tokyo_tz),
        end_time=datetime(2025, 4, 20, 14, 4, start_val_for_test, tzinfo=tokyo_tz),
        duration_in_sec=4.5,
        gathering_date=datetime(2025, 4, 20, tzinfo=tokyo_tz),
        created_at=datetime.now(tokyo_tz),
    )
    chrome_find_session_mock.return_value = pretend_domain_log
    chrome_dao.find_session = chrome_find_session_mock

    initial_write_of_program = ProgramSession(
        "path/to/foo.exe",
        "foo.exe",
        "cat",
        "hat",
        UserLocalTime(datetime(2025, 4, 20, 2, 2, 2, tzinfo=tokyo_tz)),
    )
    initial_write_of_chrome = ChromeSession("foo", "bar", datetime(2025, 4, 20, 1, 1, 1))

    # ### Act
    program_dao.push_window_ahead_ten_sec(initial_write_of_program)
    chrome_dao.push_window_ahead_ten_sec(initial_write_of_chrome)

    # Assert
    program_update_item_spy.assert_called_once()
    chrome_update_item_spy.assert_called_once()

    args, _ = program_update_item_spy.call_args
    assert isinstance(args[0], ProgramSummaryLog), "Window push failed in logging dao"

    args, _ = chrome_update_item_spy.call_args
    assert isinstance(args[0], DomainSummaryLog), "Window push failed in logging dao"


@pytest.fixture
def nonexistent_session():
    # almost certainly doesn't exist
    nonexistent_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 1, 1, 1, 0, 0, 0)))
    session = CompletedChromeSession(
        domain="github.com",
        detail="DeepSeek Chat Repository",
        start_time=nonexistent_time,
        end_time=UserLocalTime(tokyo_tz.localize(datetime(2025, 1, 1, 1, 0, 0, 1))),
        duration_for_tests=timedelta(minutes=1),
        productive=True,
    )
    return session


def test_finalize_log(prepare_daos, mock_regular_session_maker, nonexistent_session):
    """
    Confirms that for both session types:
    - The duration_in_sec is correct
    - The end_time, start_time are set correctly
    """
    program_dao, chrome_dao = prepare_daos

    tokyo_tz = pytz.timezone("Asia/Tokyo")

    # try:
    program_dao = ProgramLoggingDao(mock_regular_session_maker)
    chrome_dao = ChromeLoggingDao(mock_regular_session_maker)

    dt_utc = tokyo_tz.localize(datetime(2025, 1, 20, 12, 10, 0))
    dt = dt_utc.astimezone(tokyo_tz)  # This conversion is actually fine

    # Get the UTC offset in hours
    offset_hours = dt.utcoffset().total_seconds() / 3600  # type: ignore
    print(f"The offset for Tokyo at this time is UTC+{offset_hours}")

    # Verify if a specific offset is correct
    expected_offset = 9
    is_correct = offset_hours == expected_offset
    print(f"Is UTC+{expected_offset} correct for this time? {is_correct}")

    tokyo_offset = 9

    s1_start = tokyo_tz.localize(datetime(2025, 1, 20, 12, 10, 0))
    s1_end = s1_start + timedelta(seconds=30)
    s1_final_end = s1_start + timedelta(seconds=36)

    t4_start = tokyo_tz.localize(datetime(2025, 2, 23, 13, 10, 0))
    t5_end = t4_start + timedelta(seconds=30)
    t6_final_end = t4_start + timedelta(seconds=35)

    assert str(s1_start.tzinfo) == "Asia/Tokyo"
    assert str(s1_end.tzinfo) == "Asia/Tokyo"
    assert str(t4_start.tzinfo) == "Asia/Tokyo"
    assert str(t5_end.tzinfo) == "Asia/Tokyo"

    found_program_session = ProgramSummaryLog()
    found_program_session.start_time = convert_to_utc(s1_start)
    found_program_session.end_time = convert_to_utc(s1_end)  # They're already in UTC
    found_domain_session = DomainSummaryLog()
    found_domain_session.start_time = convert_to_utc(t4_start)
    found_domain_session.end_time = convert_to_utc(t5_end)  # They're already in UTC

    program_find_session_mock = Mock()
    program_find_session_mock.return_value = found_program_session

    chrome_find_session_mock = Mock()
    chrome_find_session_mock.return_value = found_domain_session

    program_dao.find_session = program_find_session_mock
    chrome_dao.find_session = chrome_find_session_mock

    # The all important spies
    pr_update_item_spy = Mock()
    ch_update_item_spy = Mock()
    program_dao.update_item = pr_update_item_spy
    chrome_dao.update_item = ch_update_item_spy

    # Inputs for test
    pr_delivers_end_time = CompletedProgramSession()
    pr_delivers_end_time.start_time = UserLocalTime(s1_start)
    pr_delivers_end_time.end_time = UserLocalTime(s1_final_end)

    ch_delivers_end_time = CompletedChromeSession("yadda", "yadda")
    ch_delivers_end_time.start_time = UserLocalTime(t4_start)
    ch_delivers_end_time.end_time = UserLocalTime(t6_final_end)

    assert str(pr_delivers_end_time.end_time.dt.tzinfo) == "Asia/Tokyo"
    assert str(ch_delivers_end_time.end_time.dt.tzinfo) == "Asia/Tokyo"

    # Act

    program_dao.finalize_log(pr_delivers_end_time)
    chrome_dao.finalize_log(ch_delivers_end_time)

    # Assert
    pr_update_item_spy.assert_called_once()
    ch_update_item_spy.assert_called_once()

    args, _ = pr_update_item_spy.call_args
    assert isinstance(args[0], ProgramSummaryLog)
    args, _ = ch_update_item_spy.call_args
    assert isinstance(args[0], DomainSummaryLog)

    # Assert that the end time is calculated correctly
    assert str(found_program_session.end_time.tzinfo) == "UTC"
    assert str(found_domain_session.end_time.tzinfo) == "UTC"

    s1_expected_hour = s1_final_end.hour - tokyo_offset
    s2_expected_hour = t6_final_end.hour - tokyo_offset
    assert found_program_session.end_time.hour == s1_expected_hour, "UTC conversion failed"
    assert found_domain_session.end_time.hour == s2_expected_hour, "UTC conversion failed"

    # Assert that the .duration_in_sec is calculated correctly
    program_duration = (s1_final_end - s1_start).total_seconds()
    assert found_program_session.duration_in_sec == program_duration
    chrome_duration = (t6_final_end - t4_start).total_seconds()
    assert found_domain_session.duration_in_sec == chrome_duration

    # Assert that the end_time - start_time yield is correct
    assert (
        found_program_session.end_time - found_program_session.start_time
    ).total_seconds() == program_duration
    assert (
        found_domain_session.end_time - found_domain_session.start_time
    ).total_seconds() == chrome_duration


def test_finalize_log_error(prepare_daos, mock_regular_session_maker, nonexistent_session):
    program_dao, chrome_dao = prepare_daos

    # try:
    program_dao = ProgramLoggingDao(mock_regular_session_maker)
    chrome_dao = ChromeLoggingDao(mock_regular_session_maker)

    doesnt_do_anything_mock = Mock()
    doesnt_do_anything_mock.return_value = None

    program_dao.find_session = doesnt_do_anything_mock
    chrome_dao.find_session = doesnt_do_anything_mock

    with pytest.raises(ImpossibleToGetHereError):
        program_dao.finalize_log(nonexistent_session)
    with pytest.raises(ImpossibleToGetHereError):
        chrome_dao.finalize_log(nonexistent_session)
