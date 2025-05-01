import pytest_asyncio


from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
import pytz
from sqlalchemy import text
from sqlalchemy.sql.selectable import Select


from dotenv import load_dotenv

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.models import DailyProgramSummary, Base
from surveillance.src.object.classes import CompletedProgramSession

from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime


from ....mocks.mock_clock import MockClock

load_dotenv()

tokyo_tz = pytz.timezone("Asia/Tokyo")
now_tokyo = datetime.now(pytz.UTC).astimezone(tokyo_tz)


class TestProgramSummaryDao:
    @pytest_asyncio.fixture
    async def program_summary_dao(self, mock_regular_session_maker):
        clock = SystemClock()

        logging_dao = ProgramLoggingDao(
            mock_regular_session_maker)
        program_summary_dao = ProgramSummaryDao(
            logging_dao, mock_regular_session_maker)
        yield program_summary_dao

    def test_start_session(self, program_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5, tzinfo=tokyo_tz)

        chrome = "Chrome"

        dt2 = dt + timedelta(seconds=13)
        session_data_1 = CompletedProgramSession(
            "path/to/chrome.exe", "Chrome.exe", chrome, "Facebook.com", UserLocalTime(dt), UserLocalTime(dt2))
        session_data_1.productive = False

        create_spy = Mock()
        program_summary_dao._create = create_spy

        # Act
        program_summary_dao.start_session(session_data_1)

        # Assert
        create_spy.assert_called_once()

        args, kwargs = create_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], CompletedProgramSession)
        assert isinstance(args[1], datetime)
        assert args[0].window_title == chrome
        assert args[1].day == dt.day
        assert args[1].hour == dt.hour
        assert args[1].minute == dt.minute

    def test_create(self, program_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5, tzinfo=tokyo_tz)

        add_new_item_spy = Mock()
        program_summary_dao.add_new_item = add_new_item_spy

        session_duration = 1 / 60
        window_title = "Foo!"
        dummy_session = CompletedProgramSession(
            "C:/foo.exe", "foo.exe", window_title, "detail of foo", UserLocalTime(dt))
        program_summary_dao._create(dummy_session, dt)

        add_new_item_spy.assert_called_once()

        args, kwargs = add_new_item_spy.call_args

        assert isinstance(args[0], DailyProgramSummary)

        assert args[0].program_name == window_title
        assert args[0].hours_spent == 0
        assert args[0].gathering_date.day == dt.day
        assert args[0].gathering_date.hour == 0

    def test_read_day(self, program_summary_dao, mock_session):
        # Arrange
        t0 = tokyo_tz.localize(datetime(2025, 3, 23, 9, 25, 31))
        t0_no_tz = datetime(2025, 3, 23, 9, 25, 31)

        t1 = UserLocalTime(t0 - timedelta(hours=1))
        t1_no_tz = t0 - timedelta(hours=1)
        t2 = UserLocalTime(t0 + timedelta(minutes=1))
        t3 = UserLocalTime(t0 + timedelta(minutes=5))
        t3_no_tz = t0 + timedelta(minutes=5)
        t4 = UserLocalTime(t0 + timedelta(minutes=6))

        # Pretend this happened
        # program_summary_dao.start_session(session_data, t1)
        # program_summary_dao.start_session(second_usage_by_user, t3)

        # Set up the mock session (not the session maker) to return the mock result
        first_session_out = DailyProgramSummary()
        first_session_out.program_name = "readDayTest"
        first_session_out.gathering_date = t1.dt
        first_session_out.gathering_date_local = t1_no_tz
        second_usage_out = DailyProgramSummary()
        second_usage_out.program_name = "readDayTestMaterial"
        second_usage_out.gathering_date = t3.dt
        second_usage_out.gathering_date_local = t3_no_tz

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
