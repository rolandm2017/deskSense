import pytest
import pytest_asyncio

from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text


from dotenv import load_dotenv
import os

from src.db.dao.program_summary_dao import ProgramSummaryDao

from src.db.dao.program_logs_dao import ProgramLoggingDao
from src.db.dao.chrome_logs_dao import ChromeLoggingDao
from src.db.models import DailyProgramSummary, Base
from src.object.classes import ProgramSessionData
from src.util.clock import SystemClock

from ...mocks.mock_clock import MockClock

load_dotenv()


# FIXME: OSerror
# FIXME: OSerror
# FIXME: OSerror
# FIXME: OSerror
# FIXME: OSerror

# # Get the test database connection string

# # Optional: Add error handling if the variable is required
# if ASYNC_TEST_DB_URL is None:
#     raise ValueError("TEST_DB_STRING environment variable is not set")

async def truncate_table(async_session_maker):
    """Utility function to truncate a specific table for testing purposes.
    Should ONLY be used in test environments."""
    async with async_session_maker() as session:
        async with session.begin():
            # Using raw SQL to truncate the table and reset sequences
            await session.execute(text(f'TRUNCATE TABLE program_summary_logs RESTART IDENTITY CASCADE'))
            await session.execute(text(f'TRUNCATE TABLE daily_program_summaries RESTART IDENTITY CASCADE'))


@pytest_asyncio.fixture(scope="function")
async def test_db_dao( async_engine_and_asm):
    """Create a DAO instance with the async session maker"""
    _, asm = async_engine_and_asm

    logging_dao = ProgramLoggingDao(asm)
    dao = ProgramSummaryDao(logging_dao, session_maker=asm)
    yield dao
    # Add explicit cleanup
    await truncate_table(asm)

@pytest_asyncio.fixture(autouse=True)
async def cleanup_database(async_engine_and_asm):
    """Automatically clean up the database after each test"""
    # Clean before test
    engine, asm = async_engine_and_asm
    async with asm() as session:
        await session.execute(text("DELETE FROM daily_program_summaries"))
        await session.execute(text("ALTER SEQUENCE daily_program_summaries_id_seq RESTART WITH 1"))
        await session.commit()

    yield

    # Clean after test
    try:
        async with asm() as session:
            await session.execute(text("DELETE FROM daily_program_summaries"))
            await session.execute(text("ALTER SEQUENCE daily_program_summaries_id_seq RESTART WITH 1"))
            await session.commit()
    except Exception as e:
        print(f"Error during database cleanup: {e}")


class TestProgramSummaryDao:
    @pytest.fixture
    def mock_session(self):
        """Create a mock session with necessary async methods"""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        session.get = AsyncMock()
        session.add = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_maker(self, mock_session):
        """Create session maker that handles async context management"""
        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = mock_session
        session_cm.__aexit__.return_value = None

        maker = MagicMock(spec=async_sessionmaker)
        maker.return_value = session_cm
        return maker

    @pytest.fixture
    def class_mock_dao(self, mock_session_maker):
        clock = SystemClock()

        logging_dao = ProgramLoggingDao(mock_session_maker)
        return ProgramSummaryDao(logging_dao, mock_session_maker)

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_new_entry(self, class_mock_dao, mock_session):
        # Arrange

        right_now = datetime.now()

        session_data = ProgramSessionData()
        session_data.window_title = "TestProgramFromTest"
        session_data.start_time = right_now

        # awful in-test math to produce a good start/end time for a session
        minutes = right_now.minute + 15
        if minutes >= 60:
            updated_minutes = minutes % 60
            later = right_now
            later.replace(hour=later.hour + 1, minute=updated_minutes)
        else:
            later = right_now
            later.replace(minute=minutes)

        session_data.end_time = later
        session_data.duration = later - right_now

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 0.25
        existing_entry.configure_mock(**{
            "__str__": lambda: f"DailyProgramSummary(hours_spent={existing_entry.hours_spent})"
        })

        # Mock that no existing entry is found
        mock_result = Mock()
        # Return the actual mock object
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data, right_now)

        # Assert
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_existing_entry(self, class_mock_dao, mock_session):
        # Arrange
        right_now = datetime.now()
        # session_data = {
        #     'window': 'TestProgram',
        #     'start_time': datetime.now(),
        #     'end_time': datetime.now().replace(hour=datetime.now().hour + 1)
        # }
        session_data = ProgramSessionData()
        session_data.window_title = "TestProgram"
        session_data.start_time = right_now
        later = right_now.replace(hour=datetime.now().hour + 1)
        session_data.end_time = later
        session_data.duration = later - right_now

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data, right_now)

        # Assert
        assert mock_session.execute.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_read_day(self, class_mock_dao, mock_session):
        # Arrange
        test_day = datetime.now()
        mock_entries = [
            Mock(spec=DailyProgramSummary),
            Mock(spec=DailyProgramSummary)
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = Mock()
        mock_scalar_result.all = Mock(return_value=mock_entries)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        # Act
        result = await class_mock_dao.read_day(test_day)

        # Assert
        assert result == mock_entries
        assert len(result) == len(mock_entries)
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_all(self, class_mock_dao, mock_session):
        # Arrange
        mock_entries = [
            Mock(spec=DailyProgramSummary),
            Mock(spec=DailyProgramSummary)
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = Mock()
        mock_scalar_result.all = Mock(return_value=mock_entries)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        # Act
        result = await class_mock_dao.read_all()

        # Assert
        assert result == mock_entries
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_row_for_program(self, class_mock_dao, mock_session):
        # Arrange
        program_name = "TestProgram"
        mock_entry = Mock(spec=DailyProgramSummary)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result

        # Act
        result = await class_mock_dao.read_row_for_program(program_name, datetime.now())

        # Assert
        assert result is not None
        assert result == mock_entry
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete(self, class_mock_dao, mock_session):
        # Arrange
        entry_id = 1
        mock_entry = Mock(spec=DailyProgramSummary)
        mock_session.get.return_value = mock_entry

        # Act
        result = await class_mock_dao.delete(entry_id)

        # Assert
        assert result == mock_entry
        mock_session.delete.assert_called_once_with(mock_entry)
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, class_mock_dao, mock_session):
        # Arrange
        entry_id = 1
        mock_session.get.return_value = None

        # Act
        result = await class_mock_dao.delete(entry_id)

        # Assert
        assert result is None
        mock_session.delete.assert_not_called()
        assert not mock_session.commit.called




    @pytest.mark.asyncio
    async def test_several_consecutive_writes(self, class_mock_dao, mock_session):

        # class ProgramSessionData:
        #     window_title: str
        #     detail: str
        #     start_time: datetime
        #     end_time: datetime
        #     duration: timedelta
        #     productive: bool
        dt = datetime(2025, 1, 25, 15, 5)
        # 1
        session_data_1: ProgramSessionData = ProgramSessionData()
        session_data_1.window_title = "Chrome"
        session_data_1.detail = "Facebook.com"
        session_data_1.start_time = dt
        dt2 = dt + timedelta(seconds=13)
        session_data_1.end_time = dt2
        session_data_1.productive = False
        session_data_1.duration = dt2 - dt

        # 2
        session_data_2: ProgramSessionData = ProgramSessionData()
        session_data_2.window_title = "PyCharm"
        session_data_2.detail = "some_code.py"
        session_data_2.start_time = dt2
        dt3 = dt2 + timedelta(seconds=12)
        session_data_2.end_time = dt3
        session_data_2.productive = True
        session_data_2.duration = dt3 - dt2

        # 3
        session_data_3: ProgramSessionData = ProgramSessionData()
        session_data_3.window_title = "Chrome"
        session_data_3.detail = "Facebook.com"
        session_data_3.start_time = dt3
        dt4 = dt3 + timedelta(seconds=28)
        session_data_3.end_time = dt4
        session_data_3.productive = False
        session_data_3.duration = dt4 - dt3

        # 4
        session_data_4: ProgramSessionData = ProgramSessionData()
        session_data_4.window_title = "PyCharm"
        session_data_4.detail = "MyFile.tsx"
        session_data_4.start_time = dt4
        dt5 = dt4 + timedelta(seconds=22)
        session_data_4.end_time = dt5
        session_data_4.productive = True
        session_data_4.duration = dt5 - dt4

        # 5
        session_data_5: ProgramSessionData = ProgramSessionData()
        session_data_5.window_title = "Ventrilo"
        session_data_5.detail = "Pyre - Exercises in Futility"
        session_data_5.start_time = dt5
        dt6 = dt5 + timedelta(seconds=25)
        session_data_5.end_time = dt6
        session_data_5.productive = False
        session_data_5.duration = dt6 - dt5

        # 6
        session_data_6: ProgramSessionData = ProgramSessionData()
        session_data_6.window_title = "Chrome"
        session_data_6.detail = "Claude.ai"
        session_data_6.start_time = dt6
        dt7 = dt6 + timedelta(seconds=25)
        session_data_6.end_time = dt7
        session_data_6.productive = True
        session_data_6.duration = dt7 - dt6

        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data_1, dt)
        await class_mock_dao.create_if_new_else_update(session_data_2, dt2)
        await class_mock_dao.create_if_new_else_update(session_data_3, dt3)
        await class_mock_dao.create_if_new_else_update(session_data_4, dt4)
        await class_mock_dao.create_if_new_else_update(session_data_5, dt5)
        await class_mock_dao.create_if_new_else_update(session_data_6, dt6)

        # TODO: Assert that the total time elapsed is what you expect

        # Assert
        assert mock_session.execute.call_count == 6
        assert mock_session.commit.call_count == 6
        # Clean up
        await class_mock_dao.delete_all_rows(safety_switch=True)

    @pytest.mark.asyncio
    async def test_series_of_database_operations(self, test_db_dao):

        # Get today's date
        today = datetime.now(timezone.utc).date()

        v = await test_db_dao.read_all()

        change_1 = 13
        change_2 = 12
        change_3 = 28
        change_4 = 22
        change_5 = 25
        change_6 = 25
        change_7 = 120

        # Create a datetime object for today at 3:05 PM
        dt = datetime(today.year, today.month, today.day,
                      6, 5, tzinfo=timezone.utc)
        print("base time for dt: ", dt.hour)
        dt2 = dt + timedelta(seconds=change_1)
        dt3 = dt2 + timedelta(seconds=change_2)
        dt4 = dt3 + timedelta(seconds=change_3)
        dt5 = dt4 + timedelta(seconds=change_4)
        dt6 = dt5 + timedelta(seconds=change_5)
        dt7 = dt6 + timedelta(seconds=change_6)
        dt8 = dt7 + timedelta(seconds=change_7)

        times = [dt, dt2, dt3, dt4, dt5, dt6, dt7, dt8]

        mock_clock = MockClock(times)
        test_db_dao.clock = mock_clock

        # First verify the database is empty
        initial_entries = await test_db_dao.read_all()
        print("\nInitial entries:", [
            (e.program_name, e.hours_spent) for e in initial_entries])

        # Add explicit cleanup at start of test
        async with test_db_dao.session_maker() as session:
            await session.execute(text("DELETE FROM daily_program_summaries"))
            await session.commit()

        initial_entries = await test_db_dao.read_all()
        assert len(
            initial_entries) == 0, "Database should be empty at start of test"

        chrome = "Chrome"
        pycharm = "PyCharm"
        ventrilo = "Ventrilo"
        test_vs_code = "TestPyCharm"
        chrome_time = 0
        pycharm_time = 0
        ventrilo_time = 0

        # First create a single entry and verify it works
        test_session = ProgramSessionData()
        test_session.window_title = test_vs_code
        test_session.start_time = dt
        dt_modified = dt + timedelta(minutes=5)
        test_session.end_time = dt_modified
        test_session.duration = dt_modified - dt

        await test_db_dao.create_if_new_else_update(test_session, dt)

        # Verify it was created
        entry = await test_db_dao.read_row_for_program(test_vs_code, dt)
        all = await test_db_dao.read_all()
        assert len(
            all) == 1, "Either the test entry didn't get made, or more than one was made"
        assert entry is not None
        assert entry.program_name == test_vs_code
        assert entry.hours_spent > 0

        # 1
        session_data_1: ProgramSessionData = ProgramSessionData()
        session_data_1.window_title = chrome
        session_data_1.detail = "Facebook.com"
        session_data_1.start_time = dt
        session_data_1.end_time = dt2
        session_data_1.productive = False
        session_data_1.duration = dt2 - dt
        chrome_time += change_1
        # 2
        session_data_2: ProgramSessionData = ProgramSessionData()
        session_data_2.window_title = pycharm
        session_data_2.detail = "some_code.py"
        session_data_2.start_time = dt2
        session_data_2.end_time = dt3
        session_data_2.productive = True
        session_data_2.duration = dt3 - dt2
        pycharm_time += change_2
        # 3
        session_data_3: ProgramSessionData = ProgramSessionData()
        session_data_3.window_title = chrome
        session_data_3.detail = "Facebook.com"
        session_data_3.start_time = dt3
        session_data_3.end_time = dt4
        session_data_3.productive = False
        session_data_3.duration = dt4 - dt3
        chrome_time += change_3
        # 4
        session_data_4: ProgramSessionData = ProgramSessionData()
        session_data_4.window_title = pycharm
        session_data_4.detail = "MyFile.tsx"
        session_data_4.start_time = dt4
        session_data_4.end_time = dt5
        session_data_4.productive = True
        session_data_4.duration = dt5 - dt4
        pycharm_time += change_4
        # 5
        session_data_5: ProgramSessionData = ProgramSessionData()
        session_data_5.window_title = ventrilo
        session_data_5.detail = "Pyre - Exercises in Futility"
        session_data_5.start_time = dt5
        session_data_5.end_time = dt6
        session_data_5.productive = False
        session_data_5.duration = dt6 - dt5
        ventrilo_time += change_5
        # 6
        session_data_6: ProgramSessionData = ProgramSessionData()
        session_data_6.window_title = chrome
        session_data_6.detail = "Claude.ai"
        session_data_6.start_time = dt6
        session_data_6.end_time = dt7
        session_data_6.productive = True
        session_data_6.duration = dt7 - dt6
        chrome_time += change_6
        # 7
        session_data_7: ProgramSessionData = ProgramSessionData()
        session_data_7.window_title = pycharm
        session_data_7.detail = "some_file.py"
        session_data_7.start_time = dt7
        session_data_7.end_time = dt8
        session_data_7.productive = True
        session_data_7.duration = dt8 - dt7
        pycharm_time += change_7

        sessions = [session_data_1, session_data_2, session_data_3,
                    session_data_4, session_data_5, session_data_6, session_data_7]

        unique_program_mentions = [test_vs_code, chrome, pycharm, ventrilo]

        for session in sessions:
            await test_db_dao.create_if_new_else_update(session, session.start_time)

        # ### Verify all programs were created
        all_entries = await test_db_dao.read_all()
        assert len(all_entries) == len(unique_program_mentions)

        # Verify specific program times
        # chrome_expected = 13 + 28 + 25
        # pycharm_expected = 12 + 22 + 120
        # Ventrilo_expected = 25
        TestPyCharm_expected = 5 * 60
        # expected_hours_spent = [
        #     chrome_expected, pycharm_expected, Ventrilo_expected, TestPyCharm_expected]
        expected_hours_spent = [
            chrome_time, pycharm_time, ventrilo_time, TestPyCharm_expected]
        for program in sessions:
            entry = await test_db_dao.read_row_for_program(program.window_title, program.start_time)
            assert entry is not None
            assert entry.program_name == program.window_title
            # FIXME - more specific claim pls, and passing
            assert entry.hours_spent * 3600 in expected_hours_spent
            # assert entry.hours_spent > 0.01  # FIXME - more specific claim pls, and passing

        # Test updating existing entry
        update_session = ProgramSessionData()
        update_session.window_title = chrome
        test_update_start_time = dt + timedelta(hours=3)
        test_update_end_time = dt + timedelta(hours=5)
        update_session.start_time = test_update_start_time
        update_session.end_time = test_update_end_time
        update_session.duration = test_update_end_time - test_update_start_time

        # FIXME: duration = 2 hours

        await test_db_dao.create_if_new_else_update(update_session, test_update_start_time)

        time_from_chrome_update = test_update_end_time - test_update_start_time
        time_from_chrome_update = time_from_chrome_update.total_seconds()

        # Verify the update
        chrome_entry = await test_db_dao.read_row_for_program(chrome, test_update_start_time)
        assert chrome_entry is not None
        # Original time plus update time
        assert chrome_entry.hours_spent > 2.0  # 5 - 3

        # ### Test reading by day

        right_now = dt
        day_entries = await test_db_dao.read_day(right_now)

        async with test_db_dao.session_maker() as session:
            result = await session.execute(text("SELECT program_name, gathering_date FROM daily_program_summaries"))
            rows = result.fetchall()
            for row in rows:
                print(f"Program: {row[0]}, Gathering Date: {row[1]}")
        # day_entries = await test_db_dao.read_day(dt)
        assert len(day_entries) == len(unique_program_mentions)

        # Test deletion
        if len(day_entries) > 0:
            first_entry = day_entries[0]
            deleted_entry = await test_db_dao.delete(first_entry.id)
            assert deleted_entry is not None

            # Verify deletion
            all_entries = await test_db_dao.read_all()
            assert len(all_entries) == len(unique_program_mentions) - 1

        # TEST that the total number of entries
        # reflects the number of unique programs seen
        assert len(all_entries) == 3  # Chrome, PyCharm, Ventrilo

        # TEST that the total computed time is as expected
        chrome_entry = None
        pycharm_entry = None
        ventrilo_entry = None

        for entry in all_entries:
            if entry.program_name == "Chrome":
                chrome_entry = entry
            elif entry.program_name == "PyCharm":
                pycharm_entry = entry
            elif entry.program_name == "Ventrilo":
                ventrilo_entry = entry

        #
        # # 3600 = 60 sec * 60 min = 3600 sec per hour
        #
        assert pycharm_entry is not None
        assert ventrilo_entry is not None
        assert chrome_entry is not None
        assert pycharm_entry.hours_spent == pycharm_time / 3600
        assert ventrilo_entry.hours_spent == ventrilo_time / 3600
        assert chrome_entry.hours_spent == (
            chrome_time / 3600) + (time_from_chrome_update / 3600)
