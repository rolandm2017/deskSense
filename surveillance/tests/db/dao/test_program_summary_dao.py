import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text


from dotenv import load_dotenv
import os


from surveillance.src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.models import DailyProgramSummary, Base
from src.object.classes import ProgramSessionData

# Load environment variables from .env file
load_dotenv()

# Get the test database connection string
test_db_string = os.getenv('TEST_DB_URL')

# Optional: Add error handling if the variable is required
if test_db_string is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")

print(f"Test DB Connection String: {test_db_string}")

TEST_DATABASE_URL = test_db_string


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async PostgreSQL engine for testing"""
    # Create main connection to postgres database to create/drop test db
    admin_engine = create_async_engine(
        TEST_DATABASE_URL,
        isolation_level="AUTOCOMMIT"
    )

    async with admin_engine.connect() as conn:
        # Disconnect all existing connections to test database
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'test_program_summary'
        """))

        # Drop test database if it exists and recreate it
        await conn.execute(text("DROP DATABASE IF EXISTS test_program_summary"))
        await conn.execute(text("CREATE DATABASE test_program_summary"))

    await admin_engine.dispose()

    # Create engine for test database
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False  # Set to True to see SQL queries
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield test_engine
    finally:
        await test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_async_engine(
            TEST_DATABASE_URL,
            isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'test_program_summary'
            """))
            await conn.execute(text("DROP DATABASE IF EXISTS test_program_summary"))
        await admin_engine.dispose()


@pytest.fixture(scope="function")
async def async_session_maker(async_engine):
    """Create an async session maker"""
    engine = await anext(async_engine)  # Use anext() instead of await
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return session_maker


@pytest.fixture(scope="function")
async def test_db_dao(async_session_maker):
    """Create a DAO instance with the async session maker"""
    session_maker = await async_session_maker
    dao = ProgramSummaryDao(session_maker)
    return dao


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
        return ProgramSummaryDao(mock_session_maker)

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_new_entry(self, class_mock_dao, mock_session):
        # Arrange
        # session_data = {
        #     'window': 'TestProgram',
        #     'start_time': datetime.now(),
        #     'end_time': (datetime.now().replace(hour=datetime.now().hour + 1))
        # }

        session_data = ProgramSessionData()
        session_data.window_title = "TestProgramFromTest"
        session_data.start_time = datetime.now()
        session_data.end_time = datetime.now().replace(hour=datetime.now().hour + 2)

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0
        existing_entry.__str__ = lambda self: f"DailyProgramSummary(hours_spent={
            self.hours_spent})"

        # Mock that no existing entry is found
        mock_result = Mock()
        # Return the actual mock object
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data)

        # Assert
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_existing_entry(self, class_mock_dao, mock_session):
        # Arrange
        # session_data = {
        #     'window': 'TestProgram',
        #     'start_time': datetime.now(),
        #     'end_time': datetime.now().replace(hour=datetime.now().hour + 1)
        # }
        session_data = ProgramSessionData()
        session_data.window_title = "TestProgram"
        session_data.start_time = datetime.now()
        session_data.end_time = datetime.now().replace(hour=datetime.now().hour + 1)

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data)

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

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result

        # Act
        result = await class_mock_dao.read_row_for_program(program_name)

        # Assert
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
        # 2
        session_data_2: ProgramSessionData = ProgramSessionData()
        session_data_2.window_title = "VSCode"
        session_data_2.detail = "some_code.py"
        session_data_2.start_time = dt2
        dt3 = dt2 + timedelta(seconds=12)
        session_data_2.end_time = dt3
        session_data_2.productive = True
        # 3
        session_data_3: ProgramSessionData = ProgramSessionData()
        session_data_3.window_title = "Chrome"
        session_data_3.detail = "Facebook.com"
        session_data_3.start_time = dt3
        dt4 = dt3 + timedelta(seconds=28)
        session_data_3.end_time = dt4
        session_data_3.productive = False
        # 4
        session_data_4: ProgramSessionData = ProgramSessionData()
        session_data_4.window_title = "VSCode"
        session_data_4.detail = "MyFile.tsx"
        session_data_4.start_time = dt4
        dt5 = dt4 + timedelta(seconds=22)
        session_data_4.end_time = dt5
        session_data_4.productive = True
        # 5
        session_data_5: ProgramSessionData = ProgramSessionData()
        session_data_5.window_title = "Discord"
        session_data_5.detail = "Pyre - Exercises in Futility"
        session_data_5.start_time = dt5
        dt6 = dt5 + timedelta(seconds=25)
        session_data_5.end_time = dt6
        session_data_5.productive = False
        # 6
        session_data_6: ProgramSessionData = ProgramSessionData()
        session_data_6.window_title = "Chrome"
        session_data_6.detail = "Claude.ai"
        session_data_6.start_time = dt6
        dt7 = dt6 + timedelta(seconds=25)
        session_data_6.end_time = dt7
        session_data_6.productive = True

        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await class_mock_dao.create_if_new_else_update(session_data_1)
        await class_mock_dao.create_if_new_else_update(session_data_2)
        await class_mock_dao.create_if_new_else_update(session_data_3)
        await class_mock_dao.create_if_new_else_update(session_data_4)
        await class_mock_dao.create_if_new_else_update(session_data_5)
        await class_mock_dao.create_if_new_else_update(session_data_6)

        # Assert
        assert mock_session.execute.call_count == 6
        assert mock_session.commit.call_count == 6

    @pytest.mark.asyncio
    async def test_live_database_operations(self, test_db_dao):
        test_db_dao = await test_db_dao  # Add this line back
        dt = datetime(2025, 1, 25, 15, 5)

        # First create a single entry and verify it works
        test_session = ProgramSessionData()
        test_session.window_title = "TestVSCode"
        test_session.start_time = dt
        test_session.end_time = dt + timedelta(minutes=5)

        # Add debug prints
        print("Creating first test entry...")
        print(test_db_dao, ' 35rru')
        # print(test_db_dao.session_maker(), '356ru')
        await test_db_dao.create_if_new_else_update(test_session)

        # Verify it was created
        entry = await test_db_dao.read_row_for_program("TestVSCode")
        print(f"Retrieved entry: {entry}")
        assert entry is not None
        assert entry.program_name == "TestVSCode"
        assert entry.hours_spent > 0

        # 1
        session_data_1: ProgramSessionData = ProgramSessionData()
        session_data_1.window_title = "Chrome"
        session_data_1.detail = "Facebook.com"
        session_data_1.start_time = dt
        dt2 = dt + timedelta(seconds=13)
        session_data_1.end_time = dt2
        session_data_1.productive = False
        # 2
        session_data_2: ProgramSessionData = ProgramSessionData()
        session_data_2.window_title = "VSCode"
        session_data_2.detail = "some_code.py"
        session_data_2.start_time = dt2
        dt3 = dt2 + timedelta(seconds=12)
        session_data_2.end_time = dt3
        session_data_2.productive = True
        # 3
        session_data_3: ProgramSessionData = ProgramSessionData()
        session_data_3.window_title = "Chrome"
        session_data_3.detail = "Facebook.com"
        session_data_3.start_time = dt3
        dt4 = dt3 + timedelta(seconds=28)
        session_data_3.end_time = dt4
        session_data_3.productive = False
        # 4
        session_data_4: ProgramSessionData = ProgramSessionData()
        session_data_4.window_title = "VSCode"
        session_data_4.detail = "MyFile.tsx"
        session_data_4.start_time = dt4
        dt5 = dt4 + timedelta(seconds=22)
        session_data_4.end_time = dt5
        session_data_4.productive = True
        # 5
        session_data_5: ProgramSessionData = ProgramSessionData()
        session_data_5.window_title = "Discord"
        session_data_5.detail = "Pyre - Exercises in Futility"
        session_data_5.start_time = dt5
        dt6 = dt5 + timedelta(seconds=25)
        session_data_5.end_time = dt6
        session_data_5.productive = False
        # 6
        session_data_6: ProgramSessionData = ProgramSessionData()
        session_data_6.window_title = "Chrome"
        session_data_6.detail = "Claude.ai"
        session_data_6.start_time = dt6
        dt7 = dt6 + timedelta(seconds=25)
        session_data_6.end_time = dt7
        session_data_6.productive = True
        # 7
        session_data_7: ProgramSessionData = ProgramSessionData()
        session_data_7.window_title = "VSCode"
        session_data_7.detail = "some_file.py"
        session_data_7.start_time = dt7
        dt8 = dt7 + timedelta(seconds=120)
        session_data_7.end_time = dt8
        session_data_7.productive = True

        sessions = [session_data_1, session_data_2, session_data_3,
                    session_data_4, session_data_5, session_data_6, session_data_7]

        for session in sessions:
            print(session, '405ru')
            await test_db_dao.create_if_new_else_update(session)

        # Verify all programs were created
        all_entries = await test_db_dao.read_all()
        assert len(all_entries) == len(sessions)

        # Verify specific program times
        for program in sessions:
            entry = await test_db_dao.read_row_for_program(program.window_title)
            assert entry is not None
            assert entry.program_name == program
            assert entry.hours_spent > 0

        # Test updating existing entry
        update_session = ProgramSessionData()
        update_session.window_title = "Chrome"
        update_session.start_time = dt + timedelta(hours=3)
        update_session.end_time = dt + timedelta(hours=5)
        await test_db_dao.create_if_new_else_update(update_session)

        # Verify the update
        chrome_entry = await test_db_dao.read_row_for_program("Chrome")
        assert chrome_entry is not None
        # Original time plus update time
        assert chrome_entry.hours_spent > 2.0  # 5 - 3

        # Test reading by day
        day_entries = await test_db_dao.read_day(dt)
        assert len(day_entries) == len(sessions)

        # Test deletion
        if len(day_entries) > 0:
            first_entry = day_entries[0]
            deleted_entry = await test_db_dao.delete(first_entry.id)
            assert deleted_entry is not None

            # Verify deletion
            all_entries = await test_db_dao.read_all()
            assert len(all_entries) == len(sessions) - 1

        # TEST that the total number of entries
        # reflects the number of unique programs seen
        assert len(all_entries) == 3  # Chrome, VSCode, Discord

        print(all_entries, '450ru')

        # TEST that the total computed time is as expected
        chrome = all_entries.find("Chrome")
        vs_code = all_entries.find("VSCode")
        discord = all_entries.find("Discord")
