import pytest_asyncio


from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
import pytz
from sqlalchemy import text
from sqlalchemy.sql.selectable import Select


from dotenv import load_dotenv

from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.models import DailyDomainSummary, Base
from surveillance.src.object.classes import CompletedChromeSession

from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime



load_dotenv()

tokyo_tz = pytz.timezone("Asia/Tokyo")
now_tokyo = datetime.now(pytz.UTC).astimezone(tokyo_tz)


class TestChromeSummaryDao:
    @pytest_asyncio.fixture
    async def chrome_summary_dao(self, mock_regular_session_maker):

        logging_dao = ChromeLoggingDao(
            mock_regular_session_maker)
        chrome_summary_dao = ChromeSummaryDao(
            logging_dao, mock_regular_session_maker)
        yield chrome_summary_dao

    def test_start_session(self, chrome_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5, tzinfo=tokyo_tz)


        domain_for_test = "www.facebook.com"
        dt2 = dt + timedelta(seconds=13)
        session_data_1 = CompletedChromeSession(
            domain_for_test, "Chrome.exe", UserLocalTime(dt), UserLocalTime(dt2), False)

        create_spy = Mock()
        chrome_summary_dao._create = create_spy

        # Act
        chrome_summary_dao.start_session(session_data_1)

        # Assert
        create_spy.assert_called_once()

        args, kwargs = create_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], str)
        assert isinstance(args[1], datetime)
        assert args[0] == domain_for_test
        assert args[1].day == dt.day
        assert args[1].hour == dt.hour
        assert args[1].minute == dt.minute

    def test_create(self, chrome_summary_dao):
        dt = datetime(2025, 1, 25, 15, 5, tzinfo=tokyo_tz)

        add_new_item_spy = Mock()
        chrome_summary_dao.add_new_item = add_new_item_spy

        session_duration = 1 / 60
        domain_name = "www.youtube.com"

        chrome_summary_dao._create(domain_name, dt)

        add_new_item_spy.assert_called_once()

        args, kwargs = add_new_item_spy.call_args

        assert isinstance(args[0], DailyDomainSummary)

        assert args[0].domain_name == domain_name
        assert args[0].hours_spent == 0   
        assert args[0].gathering_date.day == dt.day
        assert args[0].gathering_date.hour == 0  # Because "get start of day"

    def test_read_day(self, chrome_summary_dao, mock_session):
        # Arrange
        t0 = datetime(2025, 3, 23, 9, 25, 31, tzinfo=tokyo_tz)
        t0_no_tz = datetime(2025, 3, 23, 9, 25, 31)

        t1 = UserLocalTime(t0 - timedelta(hours=1))
        t1_no_tz = t0 - timedelta(hours=1)
        t2 = UserLocalTime(t0 + timedelta(minutes=1))
        t3 = UserLocalTime(t0 + timedelta(minutes=5))
        t3_no_tz = t0 + timedelta(minutes=5)
        t4 = UserLocalTime(t0 + timedelta(minutes=6))

        # Pretend this happened
        # chrome_summary_dao.start_session(session_data, t1)
        # chrome_summary_dao.start_session(second_usage_by_user, t3)

        # Set up the mock session (not the session maker) to return the mock result
        first_session_out = DailyDomainSummary()
        first_session_out.Chrome_name = "readDayTest"
        first_session_out.gathering_date = t1.dt
        first_session_out.gathering_date_local = t1_no_tz
        second_usage_out = DailyDomainSummary()
        second_usage_out.Chrome_name = "readDayTestMaterial"
        second_usage_out.gathering_date = t3.dt
        second_usage_out.gathering_date_local = t3_no_tz

        pretend_result = [first_session_out, second_usage_out]

        execute_and_return_all_spy = Mock()
        execute_and_return_all_spy.return_value = pretend_result
        chrome_summary_dao.execute_and_return_all = execute_and_return_all_spy

        # Act
        result = chrome_summary_dao.read_day(t1)

        # Assert
        execute_and_return_all_spy.assert_called_once()

        args, kwargs = execute_and_return_all_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], Select)

        assert len(result) == len(pretend_result)
        assert result[0].gathering_date.day == t1.day
        assert result[1].gathering_date.day == t3.day

    def test_read_all(self, chrome_summary_dao):
        # Pretend these happened:
        # chrome_summary_dao.create_if_new_else_update(session_data, t0)
        # chrome_summary_dao.create_if_new_else_update(second_session, t2)
        # chrome_summary_dao.create_if_new_else_update(third, t3)

        # Arrange
        execute_and_return_all_spy = Mock()
        execute_and_return_all_spy.return_value = [
            1, 2, 3]  # Pretend they're the right type
        chrome_summary_dao.execute_and_return_all = execute_and_return_all_spy

        # Act
        result = chrome_summary_dao.read_all()

        # Assert
        execute_and_return_all_spy.assert_called_once()

        args, kwargs = execute_and_return_all_spy.call_args
        # Check that first argument is a Select object
        assert isinstance(args[0], Select)
        assert len(result) == 3
