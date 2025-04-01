import pytest
import pytest_asyncio

from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text


from dotenv import load_dotenv
import os

from src.db.dao.direct.program_summary_dao import ProgramSummaryDao

from src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from src.db.models import DailyProgramSummary, Base
from src.object.classes import ProgramSessionData
from src.util.clock import SystemClock

from ....mocks.mock_clock import MockClock

load_dotenv()

import psutil

process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)
print(f"Num of open files: {num_open_files}")

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
    await logging_dao.cleanup()
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
    @pytest_asyncio.fixture
    async def program_summary_dao(self, plain_asm):
        clock = SystemClock()

        logging_dao = ProgramLoggingDao(plain_asm)
        program_summary_dao = ProgramSummaryDao(logging_dao, plain_asm)
        yield program_summary_dao
        await logging_dao.cleanup()

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_new_entry(self, program_summary_dao):
    # async def test_create_if_new_else_update_new_entry(self, class_mock_dao, mock_session):
        # Arrange

        time_for_test = datetime(2025, 3, 23, 9, 25, 25)

        # FIXME: No longer rely on now(); instead, set a fixed time, so your test doesn't depend
        # on what time it is

        session_data = ProgramSessionData()
        session_data.window_title = "TestProgramFromTest"
        session_data.start_time = time_for_test

        # awful in-test math to produce a good start/end time for a session
        later = time_for_test + timedelta(minutes=3)

        session_data.end_time = later
        session_data.duration = later - time_for_test

        # Act
        await program_summary_dao.create_if_new_else_update(session_data, time_for_test)

        # ### Assert
        # Check if it's really in there
        all = await program_summary_dao.read_all()
        assert len(all) == 1, "Expected exactly one row"
        percent_of_hour = all[0].hours_spent

        assert session_data.duration.seconds / (60 * 60) == percent_of_hour

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_existing_entry(self, program_summary_dao):
        # Arrange
        t0 = datetime(2025, 3, 23, 9, 25, 31)

        t0 = t0 - timedelta(hours=1)
        t1 = t0 + timedelta(minutes=1)
        t2 = t0 + timedelta(minutes=5)
        t3 = t0 + timedelta(minutes=6)
        # session_data = {
        #     'window': 'TestProgram',
        #     'start_time': datetime.now(),
        #     'end_time': datetime.now().replace(hour=datetime.now().hour + 1)
        # }
        session_data = ProgramSessionData()
        session_data.window_title = "ExistingEntryTestSession"
        session_data.start_time = t0
        session_data.end_time = t1
        session_data.duration = t1 - t0

        second_usage_by_user = ProgramSessionData()
        second_usage_by_user.window_title = "ExistingEntryTestSession"
        second_usage_by_user.start_time = t2
        second_usage_by_user.end_time = t3
        second_usage_by_user.duration = t3 - t2

        # Arranging still: This session is already in there
        await program_summary_dao.create_if_new_else_update(session_data, t0)

        # Create a spy for the create method
        original_create = program_summary_dao._create
        create_spy = AsyncMock()
        program_summary_dao._create = create_spy
        
        # Also spy on update_hours
        original_update_hours = program_summary_dao.update_hours
        update_spy = AsyncMock()
        program_summary_dao.update_hours = update_spy

        # Act
        await program_summary_dao.create_if_new_else_update(second_usage_by_user, t2)

        # Assert
        create_spy.assert_not_called()
        update_spy.assert_called_once()
        # assert mock_session.execute.called
        # assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_read_day(self, program_summary_dao):
        # Arrange
        t0 = datetime(2025, 3, 23, 9, 25, 31)

        t0 = t0 - timedelta(hours=1)
        t1 = t0 + timedelta(minutes=1)
        t2 = t0 + timedelta(minutes=5)
        t3 = t0 + timedelta(minutes=6)
        session_data = ProgramSessionData("readDayTest", "", t0, t1)

        second_usage_by_user = ProgramSessionData("readDayTestMaterial", "", t2, t3)

        await program_summary_dao.create_if_new_else_update(session_data, t0)
        await program_summary_dao.create_if_new_else_update(second_usage_by_user, t2)
        

        # Act
        result = await program_summary_dao.read_day(t0)

        # Assert
        assert len(result) == len([session_data, second_usage_by_user])
        assert result[0].gathering_date.day == t0.day
        assert result[1].gathering_date.day == t0.day

    @pytest.mark.asyncio
    async def test_read_all(self, program_summary_dao):
        # Arrange
        t0 = datetime(2025, 3, 23, 9, 25, 39)

        t0 = t0 - timedelta(hours=1)
        t1 = t0 + timedelta(minutes=1)
        t2 = t0 + timedelta(minutes=5)
        t3 = t0 + timedelta(minutes=6)
        t4 = t0 + timedelta(minutes=8)
        session_data = ProgramSessionData("readAllTest", "", t0, t1)

        second_session = ProgramSessionData("readAllTestMaterial", "", t2, t3)
        third = ProgramSessionData("readAllTestMaterialAgain", "", t3, t4)

        await program_summary_dao.create_if_new_else_update(session_data, t0)
        await program_summary_dao.create_if_new_else_update(second_session, t2)
        await program_summary_dao.create_if_new_else_update(third, t3)

        # Act
        result = await program_summary_dao.read_all()

        # Assert
        assert len(result) == 3


    @pytest.mark.asyncio
    async def test_read_row_for_program(self, program_summary_dao):
        # Arrange
        program_name = "TestProgram"
        
        t0 = datetime(2025, 3, 23, 8, 25, 41)
        t0 = t0 - timedelta(hours=1)
        t1 = t0 + timedelta(minutes=1)
        session = ProgramSessionData(program_name, "", t0, t1)
        await program_summary_dao.create_if_new_else_update(session, t0)

        # Act
        result = await program_summary_dao.read_row_for_program(program_name, t0)

        # Assert
        duration_as_percent_of_hour = (t1 - t0).seconds / (60 * 60)
        assert result is not None
        assert result.program_name == session.window_title
        assert result.hours_spent == duration_as_percent_of_hour

    # YAGNI:
    # @pytest.mark.asyncio
    # async def test_delete(self, class_mock_dao, mock_session):
        # pass
    # YAGNI:
    # @pytest.mark.asyncio
    # async def test_delete_nonexistent(self, class_mock_dao, mock_session):
        # pass

    @pytest.mark.asyncio
    async def test_several_consecutive_writes(self, program_summary_dao):

        dt = datetime(2025, 1, 25, 15, 5)
        # 1

        chrome = "Chrome"
        pycharm = "PyCharm"
        ventrilo = "Venrilo"
        
        dt2 = dt + timedelta(seconds=13)
        session_data_1 = ProgramSessionData(chrome, "Facebook.com", dt, dt2)
        session_data_1.productive = False
    
        # 2
        dt3 = dt2 + timedelta(seconds=12)
        session_data_2 = ProgramSessionData(pycharm, "some_code.py", dt2, dt3)
        session_data_2.productive = True

        # 3
        dt4 = dt3 + timedelta(seconds=28)
        session_data_3 = ProgramSessionData(chrome, "Facebook.com", dt3, dt4)
        session_data_3.productive = False

        # 4
        dt5 = dt4 + timedelta(seconds=22)
        session_data_4 = ProgramSessionData(pycharm, "MyFile.tsx", dt4, dt5)
        session_data_4.productive = True

        # 5
        dt6 = dt5 + timedelta(seconds=25)
        session_data_5 = ProgramSessionData(ventrilo, "Pyre - Exercises in Futility", dt5, dt6)
        session_data_5.productive = False
        

        # 6
        dt7 = dt6 + timedelta(seconds=25)
        session_data_6 = ProgramSessionData(chrome, "Claude.ai", dt6, dt7)
        session_data_6.productive = True

        chrome_count = 3
        pycharm_count = 2
        ventrilo_count = 1

        total_time = (13 + 12 + 28 + 22 + 25 + 25) / (60 * 60)

        # Act
        await program_summary_dao.create_if_new_else_update(session_data_1, dt)
        await program_summary_dao.create_if_new_else_update(session_data_2, dt2)
        await program_summary_dao.create_if_new_else_update(session_data_3, dt3)
        await program_summary_dao.create_if_new_else_update(session_data_4, dt4)
        await program_summary_dao.create_if_new_else_update(session_data_5, dt5)
        await program_summary_dao.create_if_new_else_update(session_data_6, dt6)

        # TODO: Assert that the total time elapsed is what you expect

        # Assert
        all = await program_summary_dao.read_all()
        total = sum(x.hours_spent for x in all)
        assert len(all) == 3 
        assert total == total_time

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
        session_data_1 = ProgramSessionData(chrome, "Facebook.com", dt, dt2)
        session_data_1.productive = False
        chrome_time += change_1
        # 2
        dt3 = dt2 + timedelta(seconds=12)
        session_data_2 = ProgramSessionData(pycharm, "some_code.py", dt2, dt3)
        session_data_2.productive = True
        pycharm_time += change_2

        # 3
        dt4 = dt3 + timedelta(seconds=28)
        session_data_3 = ProgramSessionData(chrome, "Facebook.com", dt3, dt4)
        session_data_3.productive = False
        chrome_time += change_3

        # 4
        dt5 = dt4 + timedelta(seconds=22)
        session_data_4 = ProgramSessionData(pycharm, "MyFile.tsx", dt4, dt5)
        session_data_4.productive = True
        pycharm_time += change_4

        # 5
        dt6 = dt5 + timedelta(seconds=25)
        session_data_5 = ProgramSessionData(ventrilo, "Pyre - Exercises in Futility", dt5, dt6)
        session_data_5.productive = False
        ventrilo_time += change_5

        # 6
        dt7 = dt6 + timedelta(seconds=25)
        session_data_6 = ProgramSessionData(chrome, "Claude.ai", dt6, dt7)
        session_data_6.productive = True
        chrome_time += change_6

        # 7
        dt8 = dt7 + timedelta(seconds=30)
        session_data_7 = ProgramSessionData(pycharm, "some_file.py", dt7, dt8)
        session_data_7.productive = True
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
        chrome_expected = (13 + 28 + 25) / (60 * 60)
        ventrilo_expected = 25 / (60 * 60)
        pyCharm_expected = (12 + 22 + 30) / (60 * 60)
        # expected_hours_spent = [
        #     chrome_expected, pycharm_expected, Ventrilo_expected, TestPyCharm_expected]
        expected_hours_spent = [
            chrome_expected, ventrilo_expected, pyCharm_expected]
        for program in sessions:
            entry = await test_db_dao.read_row_for_program(program.window_title, program.start_time)
            assert entry is not None
            assert entry.program_name == program.window_title
            # FIXME - more specific claim pls, and passing
            assert entry.hours_spent in expected_hours_spent
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
        assert pycharm_entry.hours_spent == pyCharm_expected
        assert ventrilo_entry.hours_spent == ventrilo_expected
        assert chrome_entry.hours_spent == (
            chrome_time / 3600) + (time_from_chrome_update / 3600)

