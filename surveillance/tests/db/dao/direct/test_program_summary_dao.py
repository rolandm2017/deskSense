import psutil
import pytest
import pytest_asyncio


from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlalchemy.sql.selectable import Select


from dotenv import load_dotenv

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.models import DailyProgramSummary, Base
from surveillance.src.object.classes import ProgramSession

from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime


from ....mocks.mock_clock import MockClock

load_dotenv()


process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)
print(f"Num of open files: {num_open_files}")


class TestProgramSummaryDao:
    @pytest_asyncio.fixture
    async def program_summary_dao(self, mock_regular_session_maker, mock_async_session_maker):
        clock = SystemClock()

        logging_dao = ProgramLoggingDao(
            mock_regular_session_maker)
        program_summary_dao = ProgramSummaryDao(
            logging_dao, mock_regular_session_maker, mock_async_session_maker)
        yield program_summary_dao

    def test_start_session(self, program_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5)

        chrome = "Chrome"

        dt2 = dt + timedelta(seconds=13)
        session_data_1 = ProgramSession(
            "path/to/chrome.exe", "Chrome.exe", chrome, "Facebook.com", dt, dt2)
        session_data_1.productive = False

        create_spy = Mock()
        program_summary_dao._create = create_spy

        # Act
        program_summary_dao.start_session(session_data_1, UserLocalTime(dt))

        # Assert
        create_spy.assert_called_once()

        args, kwargs = create_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], ProgramSession)
        assert isinstance(args[1], float)
        assert isinstance(args[2], datetime)
        assert args[0].window_title == chrome
        assert args[1] == 10 / SECONDS_PER_HOUR
        assert args[2].day == dt.day
        assert args[2].hour == 0
        assert args[2].minute == 0

    def test_create(self, program_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5)

        add_new_item_spy = Mock()
        program_summary_dao.add_new_item = add_new_item_spy

        session_duration = 1 / 60
        window_title = "Foo!"
        dummy_session = ProgramSession(
            "C:/foo.exe", "foo.exe", window_title, "detail of foo", dt)
        program_summary_dao._create(dummy_session, session_duration, dt)

        add_new_item_spy.assert_called_once()

        args, kwargs = add_new_item_spy.call_args

        assert isinstance(args[0], DailyProgramSummary)

        assert args[0].program_name == window_title
        assert args[0].hours_spent == session_duration
        assert args[0].gathering_date.day == dt.day
        assert args[0].gathering_date.hour == dt.hour

    def test_read_day(self, program_summary_dao, mock_session):
        # Arrange
        t0 = datetime(2025, 3, 23, 9, 25, 31)

        t1 = UserLocalTime(t0 - timedelta(hours=1))
        t2 = UserLocalTime(t0 + timedelta(minutes=1))
        t3 = UserLocalTime(t0 + timedelta(minutes=5))
        t4 = UserLocalTime(t0 + timedelta(minutes=6))

        # Pretend this happened
        # program_summary_dao.start_session(session_data, t1)
        # program_summary_dao.start_session(second_usage_by_user, t3)

        # Set up the mock session (not the session maker) to return the mock result
        first_session_out = DailyProgramSummary()
        first_session_out.program_name = "readDayTest"
        first_session_out.gathering_date = t1.dt
        second_usage_out = DailyProgramSummary()
        second_usage_out.program_name = "readDayTestMaterial"
        second_usage_out.gathering_date = t3.dt

        pretend_result = [first_session_out, second_usage_out]

        execute_and_return_all_spy = Mock()
        execute_and_return_all_spy.return_value = pretend_result
        program_summary_dao.execute_and_return_all = execute_and_return_all_spy

        # Act
        result = program_summary_dao.read_day(t1)

        # Assert
        execute_and_return_all_spy.assert_called_once()

        args, kwargs = execute_and_return_all_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], Select)

        assert len(result) == len(pretend_result)
        assert result[0].gathering_date.day == t1.day
        assert result[1].gathering_date.day == t3.day

    def test_read_all(self, program_summary_dao):
        # Pretend these happened:
        # program_summary_dao.create_if_new_else_update(session_data, t0)
        # program_summary_dao.create_if_new_else_update(second_session, t2)
        # program_summary_dao.create_if_new_else_update(third, t3)

        # Arrange
        execute_and_return_all_spy = Mock()
        execute_and_return_all_spy.return_value = [
            1, 2, 3]  # Pretend they're the right type
        program_summary_dao.execute_and_return_all = execute_and_return_all_spy

        # Act
        result = program_summary_dao.read_all()

        # Assert
        execute_and_return_all_spy.assert_called_once()

        args, kwargs = execute_and_return_all_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], Select)
        assert len(result) == 3

    def test_read_row_for_program(self, program_summary_dao):
        # Arrange
        program_name = "TestProgram"

        t0 = datetime(2025, 3, 23, 8, 25, 41)
        # t0 = t0 - timedelta(hours=1)
        # t1 = t0 + timedelta(minutes=1)
        # session = ProgramSession(program_name, "", t0, t1)
        # program_summary_dao.create_if_new_else_update(session, t0)

        execute_and_one_or_none_spy = Mock()
        program_summary_dao.execute_and_read_one_or_none = execute_and_one_or_none_spy

        # Act
        program_summary_dao.read_row_for_program(
            program_name, UserLocalTime(t0))

        # Assert
        execute_and_one_or_none_spy.assert_called_once()

        args, kwargs = execute_and_one_or_none_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], Select)
