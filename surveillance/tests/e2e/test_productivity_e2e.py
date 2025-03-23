
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from datetime import datetime

from dotenv import load_dotenv
import os

from src.arbiter.activity_arbiter import ActivityArbiter
from src.arbiter.activity_recorder import ActivityRecorder
from src.db.models import DailyProgramSummary, Base
from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.chrome_summary_dao import ChromeSummaryDao
from src.db.dao.summary_logs_dao import ChromeLoggingDao, ProgramLoggingDao
from src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

from src.services.chrome_service import ChromeService
from src.service_dependencies import get_dashboard_service


from src.surveillance_manager import FacadeInjector, SurveillanceManager
from surveillance.src.object.classes import ChromeSessionData, ProgramSessionData
from surveillance.src.util.program_tools import separate_window_name_and_detail

from ..mocks.mock_clock import MockClock
from ..data.captures_for_test_data_Chrome import chrome_data
from ..data.captures_for_test_data_programs import program_data


# TODO: Test the program facade to the database,
# and the Chrome service to the database,
# and then after a dozen of those,
# go from the database to the Productivity Summary, leisure:productivity

"""
The ultimate goal of this e2e test is to track down a bug in
get_weekly_productivity_overview
that is yielding like 28 hour days from 8 hours of usage.

The test must start from the facade.

This e2e uses the test database, but the facade all the way to 
the dashboard service endpoint, should be very real data, no breaks except to assert midway through.
"""

load_dotenv()

ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

if ASYNC_TEST_DB_URL is None:
    raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if ASYNC_TEST_DB_URL is None:
        raise ValueError("ASYNC_TEST_DB_URL was None")
    default_url = ASYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_async_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    async with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await conn.execute(text("CREATE DATABASE dsTestDb"))

    await admin_engine.dispose()

    # Create engine for test database
    test_engine = create_async_engine(
        ASYNC_TEST_DB_URL,
        # echo=True,
        isolation_level="AUTOCOMMIT"  # Add this
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
            default_url,  # Connect to default db for cleanup
            isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await admin_engine.dispose()


@pytest.fixture(scope="function")
def sync_engine():
    """Create a synchronous PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if SYNC_TEST_DB_URL is None:
        raise ValueError("SYNC_TEST_DB_URL was None")

    from sqlalchemy import create_engine, text

    # Extract the default postgres database URL
    default_url = SYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        conn.execute(text("CREATE DATABASE dsTestDb"))

    admin_engine.dispose()

    # Create engine for test database
    test_engine = create_engine(
        # pool_pre_ping resolves a bug
        SYNC_TEST_DB_URL, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

    # Create all tables
    with test_engine.begin() as conn:
        Base.metadata.create_all(conn)

    try:
        yield test_engine
    finally:
        test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_engine(
            default_url,
            isolation_level="AUTOCOMMIT"
        )
        with admin_engine.connect() as conn:
            conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        admin_engine.dispose()


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
def shutdown_session_maker(sync_engine):
    """Create a synchronous session maker"""
    from sqlalchemy.orm import sessionmaker

    session_maker = sessionmaker(
        sync_engine,
        expire_on_commit=False
    )

    # session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # shutdown_session_maker = scoped_session(session_factory)
    return session_maker


#       oooox
#     oox   oox
#    ox       ox
#   ox         ox
#   ox         ox
#   ox         ox
#    ox       ox
#     oox   oox
#       oooox
#
# First, events are recorded.

@pytest.mark.asyncio
async def test_recording_and_reading_sessions(async_session_maker, shutdown_session_maker):

    program_facade = Mock()

    real_program_events = [x["event"] for x in program_data]
    real_chrome_events = chrome_data

    times_for_program_events = [x["time"] for x in program_data]

    program_durations = []

    for i in range(0, len(times_for_program_events)):
        if i == len(times_for_program_events) - 1:
            break
        current = datetime.fromisoformat(times_for_program_events[i])
        next_event = datetime.fromisoformat(times_for_program_events[i + 1])
        change = next_event - current
        program_durations.append(change)

    program_facade.listen_for_window_changes.side_effect = real_program_events

    program_logging_dao = ProgramLoggingDao(async_session_maker)
    chrome_logging_dao = ChromeLoggingDao(async_session_maker)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, async_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, async_session_maker)

    # Create spies on the DAOs' create_if_new_else_update methods
    program_summary_spy = Mock(
        side_effect=program_summary_dao.create_if_new_else_update)
    program_summary_dao.create_if_new_else_update = program_summary_spy

    chrome_summary_spy = Mock(
        side_effect=chrome_summary_dao.create_if_new_else_update)
    chrome_summary_dao.create_if_new_else_update = chrome_summary_spy

    clock_again = MockClock([])

    activity_recorder = ActivityRecorder(
        clock_again, program_summary_dao, chrome_summary_dao)

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, program_facade)
    # TODO: async session from the test db
    clock = MockClock([])
    activity_arbiter = ActivityArbiter(clock)

    activity_arbiter.add_summary_dao_listener(activity_recorder)

    # Create a spy on the notify_summary_dao method
    notify_summary_dao_spy = Mock(
        side_effect=activity_arbiter.notify_summary_dao)
    activity_arbiter.notify_summary_dao = notify_summary_dao_spy

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    chrome_svc = ChromeService(clock, activity_arbiter)
    surveillance_manager = SurveillanceManager(
        async_session_maker, shutdown_session_maker, chrome_svc, activity_arbiter, facades)

    create_spy = Mock(side_effect=surveillance_manager.program_dao.create)
    surveillance_manager.program_dao.create = create_spy

    # Prevent odd shutdown triggers from firing when tests close
    surveillance_manager.system_tracker = None  # type: ignore

    # Checkpoint:
    # The Arbiter was called with the expected values
    assert spy_on_set_program_state.call_count == len(real_program_events) - 1
    # The DAO was called with the expected values
    assert create_spy.call_count == len(real_program_events) - 1

    # Checkpoint:
    # The Arbiter recorded the expected *number* of times
    assert notify_summary_dao_spy.call_count == len(real_program_events)
    # The Arbiter recorded the expected total amount of time
    # TODO
    # The DAOS recorded the expected number of times
    expected_program_call_count = len(real_program_events)
    expected_chrome_call_count = len(real_chrome_events)
    assert program_summary_spy.call_count > 0
    assert chrome_summary_spy.call_count > 0

    assert program_summary_spy.call_count == expected_program_call_count
    assert chrome_summary_spy.call_count == expected_chrome_call_count
    # The DAOs recorded the expected amount of time
    # Check the arguments that were passed were as expected
    # NOTE:
    # [0][0][0] -> program_session: ProgramSessionData,
    # [0][0][1] -> right_now: datetime
    for i in range(len(real_program_events)):
        program_session_arg = program_summary_spy.call_args_list[i][0][0]
        right_now_arg = program_summary_spy.call_args_list[i][0][1]
        assert isinstance(program_session_arg, ProgramSessionData)
        assert isinstance(right_now_arg, datetime)

        # Transformation happens in the ProgramTracker:
        # detail, window = separate_window_name_and_detail(
        #     window_change_dict["window_title"])
        # new_session.window_title = window
        # new_session.detail = detail

        detail, window = separate_window_name_and_detail(
            real_program_events[i]["window_title"])

        assert program_session_arg.window_title == window
        assert program_session_arg.duration == program_durations[i]

    for i in range(len(real_chrome_events)):
        chrome_arg = chrome_summary_spy.call_args_list[i][0][0]
        right_now_arg = chrome_summary_spy.call_args_list[i][0][1]
        assert isinstance(chrome_arg, ChromeSessionData)
        assert isinstance(right_now_arg, datetime)

        assert chrome_arg.domain == real_chrome_events[i].url

    # Checkpoint:
    # Dashboard Service reports the right amount of time for get_weekly_productivity_overview
    dashboard_service = await get_dashboard_service()

# Then, we check that the events are there as planned.

# Second, we request the full week of productivity as a summary.

# We verify that the total hours are as expected


#     /\
#    /  \
#   /    \
#  /      \
# /________\
#
#  #  #  #  #


#      @@@@@
#     @@@@@@@
#    @@@@@@@@@
#   @@@@@@@@@@@
#  @@@@@@@@@@@@@
# @@@@@@@@@@@@@@@
#      |||||
#      |||||
#      |||||
# ~~~~~~~~~~~~~~
