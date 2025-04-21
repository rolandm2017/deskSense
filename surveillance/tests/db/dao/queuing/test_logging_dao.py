import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from sqlalchemy.sql.selectable import Select


from sqlalchemy import text

import pytz
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone


from dotenv import load_dotenv
import os

# FIXME:
# FIXME: Task was destroyed but it is pending! ``
# FIXME: Task was destroyed but it is pending!
# FIXME:

from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog, Base


from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.util.time_formatting import convert_to_utc
from surveillance.src.util.errors import ImpossibleToGetHereError
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.time_wrappers import UserLocalTime


timezone_for_test_data = ZoneInfo('America/New_York')

load_dotenv()


@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(mock_regular_session_maker, mock_async_session):
    """Create the necessary DAO instances for session integrity testing"""
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(
        mock_regular_session_maker, mock_async_session)
    chrome_logging_dao = ChromeLoggingDao(
        mock_regular_session_maker, mock_async_session)

    return {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
    }


@pytest.fixture
def mock_session_data():
    test_program_session = ProgramSession(
        "Ventrilo",
        "The Programmer's Hangout",
        start_time=UserLocalTime(datetime(2025, 2, 1, 1, 0, 4, 0,
                                          tzinfo=timezone_for_test_data)),
        productive=False
    )

    test_chrome_session = ChromeSession(
        "chatgpt.com",
        "gpt Chat Repository",
        UserLocalTime(datetime(2025, 2, 1, 1, 0, 5, 0,
                      tzinfo=timezone_for_test_data)),
        duration_for_tests=timedelta(minutes=1),
        productive=True
    )

    return test_program_session, test_chrome_session


@pytest_asyncio.fixture
async def prepare_daos(mock_regular_session_maker, mock_async_session):
    program_dao = ProgramLoggingDao(
        mock_regular_session_maker, mock_async_session)
    chrome_dao = ChromeLoggingDao(
        mock_regular_session_maker, mock_async_session)

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

    pr_find_one_mock = Mock()
    ch_find_one_mock = Mock()
    program_dao.find_one_or_none = pr_find_one_mock
    chrome_dao.find_one_or_none = ch_find_one_mock

    pr_select_where_time_equals_spy = Mock(
        side_effect=program_dao.select_where_time_equals)
    ch_select_where_time_equals_spy = Mock(
        side_effect=chrome_dao.select_where_time_equals)
    program_dao.select_where_time_equals = pr_select_where_time_equals_spy
    chrome_dao.select_where_time_equals = ch_select_where_time_equals_spy

    pr_time_as_utc = convert_to_utc(program_session.start_time)
    ch_time_as_utc = convert_to_utc(chrome_session.start_time)

    # ### Act
    _ = program_dao.find_session(program_session)
    _ = chrome_dao.find_session(chrome_session)

    pr_select_where_time_equals_spy.assert_called_with(
        pr_time_as_utc)
    ch_select_where_time_equals_spy.assert_called_with(
        ch_time_as_utc)

    args, _ = pr_find_one_mock.call_args

    assert isinstance(args[0], Select)

    args, _ = ch_find_one_mock.call_args

    assert isinstance(args[0], Select)

# # TODO: Manually drop the tables


def test_push_window_ahead(prepare_daos, mock_session_data):
    """Test assumes there is an existing session, which the test can 'push the window forward' for."""
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos
    # chrome_dao = ChromeLoggingDao(plain_asm)

    program_merge_item_spy = Mock()
    program_dao.merge_item = program_merge_item_spy

    chrome_merge_item_spy = Mock()
    chrome_dao.merge_item = chrome_merge_item_spy

    start_val_for_test = 33

    program_find_session_mock = Mock()
    pretend_pr_log = ProgramSummaryLog(
        program_name="VSCode",
        hours_spent=120 / SECONDS_PER_HOUR,
        start_time=datetime(2025, 4, 19, 9, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2025, 4, 19, 17, 0,
                          start_val_for_test, tzinfo=timezone.utc),
        duration=8.0,
        created_at=datetime.now(timezone.utc),
        gathering_date=datetime(2025, 4, 19, tzinfo=timezone.utc)
    )
    program_find_session_mock.return_value = pretend_pr_log
    program_dao.find_session = program_find_session_mock

    chrome_find_session_mock = Mock()
    pretend_domain_log = DomainSummaryLog(
        domain_name="example.com",
        hours_spent=4.5,
        start_time=datetime(2025, 4, 20, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2025, 4, 20, 14, 4, start_val_for_test,
                          tzinfo=timezone.utc),
        duration=4.5,
        gathering_date=datetime(2025, 4, 20, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    chrome_find_session_mock.return_value = pretend_domain_log
    chrome_dao.find_session = chrome_find_session_mock

    initial_write_of_program = ProgramSession(
        "cat", "hat", datetime(2025, 4, 20, 2, 2, 2))
    initial_write_of_chrome = ChromeSession(
        "foo", "bar", datetime(2025, 4, 20, 1, 1, 1))

    # ### Act
    program_dao.push_window_ahead_ten_sec(initial_write_of_program)
    chrome_dao.push_window_ahead_ten_sec(initial_write_of_chrome)

    # Assert
    program_merge_item_spy.assert_called_once()
    chrome_merge_item_spy.assert_called_once()

    args, _ = program_merge_item_spy.call_args
    assert isinstance(args[0], ProgramSummaryLog)
    len_of_window_push = 10  # sec
    assert args[0].end_time.second == start_val_for_test + len_of_window_push

    args, _ = chrome_merge_item_spy.call_args
    assert isinstance(args[0], DomainSummaryLog)
    len_of_window_push = 10  # sec
    assert args[0].end_time.second == start_val_for_test + len_of_window_push


@pytest.fixture
def nonexistent_session():
    # almost certainly doesn't exist
    nonexistent_time = datetime(2025, 1, 1, 1, 0, 0, 0)
    session = ChromeSession(domain="github.com",
                            detail="DeepSeek Chat Repository",
                            start_time=nonexistent_time,
                            end_time=datetime(2025, 1, 1, 1, 0, 0, 1),
                            duration_for_tests=timedelta(minutes=1),
                            productive=True)
    return session


def test_finalize_log_error(prepare_daos, mock_regular_session_maker, mock_async_session, nonexistent_session):
    program_dao, chrome_dao = prepare_daos

    # try:
    program_dao = ProgramLoggingDao(
        mock_regular_session_maker, mock_async_session)
    chrome_dao = ChromeLoggingDao(
        mock_regular_session_maker, mock_async_session)

    doesnt_do_anything_mock = Mock()
    doesnt_do_anything_mock.return_value = None

    program_dao.find_session = doesnt_do_anything_mock
    chrome_dao.find_session = doesnt_do_anything_mock

    with pytest.raises(ImpossibleToGetHereError):
        program_dao.finalize_log(nonexistent_session)
    with pytest.raises(ImpossibleToGetHereError):
        chrome_dao.finalize_log(nonexistent_session)
    # finally:
    #     await truncate_test_tables(plain_asm)
