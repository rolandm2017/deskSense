import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from surveillance.src.db.models import TimelineEntryObj, Base
from surveillance.src.object.enums import ChartEventType
from dotenv import load_dotenv
import os
load_dotenv()


# Use a test database URL
TEST_DATABASE_URL = os.getenv(
    'TEST_DB_URL')

print(TEST_DATABASE_URL[:6])
# Or use an in-memory SQLite database for testing
# TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# Update engine creation
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False
)

# Update session maker to use async
Session = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession
)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session():
    """Create a fresh sqlalchemy session for each test."""
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_timeline_entry_mouse_event(db_session):  # Removed async marker
    """Test creation of a mouse event timeline entry."""
    now = datetime.now()
    mouse_event = TimelineEntryObj(
        group=ChartEventType.MOUSE,
        start=now,
        end=now
    )

    db_session.add(mouse_event)
    db_session.commit()
    db_session.refresh(mouse_event)

    # Query all entries
    all_entries = db_session.query(TimelineEntryObj).all()
    print(all_entries)

    # Verify the computed columns
    assert mouse_event.clientFacingId == f"mouse-{mouse_event.id}"
    assert mouse_event.content == f"Mouse Event {mouse_event.id}"

    entries = db_session.query(TimelineEntryObj).all()

    assert len(entries) == 1

    my_mouse_event = entries[0]

    assert my_mouse_event.id == 1
    # and hence:
    assert my_mouse_event.clientFacingId == "mouse-1"
    assert my_mouse_event.content == "Mouse Event 1"

    now = datetime.now()
    another_event = TimelineEntryObj(
        group=ChartEventType.MOUSE,
        start=now,
        end=now
    )

    db_session.add(another_event)
    db_session.commit()
    db_session.refresh(another_event)

    entries = db_session.query(TimelineEntryObj).all()

    assert len(entries) == 2

    assert another_event.id == 2
    assert another_event.clientFacingId == "mouse-2"
    assert another_event.content == "Mouse Event 2"


def test_timeline_entry_keyboard_event(db_session):
    """Test creation of a keyboard event timeline entry."""
    # Create a keyboard event
    now = datetime.now()
    keyboard_event = TimelineEntryObj(
        group=ChartEventType.KEYBOARD,
        start=now,
        end=now
    )

    db_session.add(keyboard_event)
    db_session.commit()
    db_session.refresh(keyboard_event)

    # Verify the computed columns
    assert keyboard_event.id is not None and keyboard_event.id >= 0
    assert keyboard_event.clientFacingId == f"keyboard-{keyboard_event.id}"
    assert keyboard_event.content == f"Typing Session {keyboard_event.id}"


def test_multiple_timeline_entries(db_session):
    """Test creation of multiple timeline entries and verify their IDs are unique."""
    now = datetime.now()

    # Create multiple events
    events = [
        TimelineEntryObj(group=ChartEventType.MOUSE, start=now, end=now),
        TimelineEntryObj(group=ChartEventType.KEYBOARD, start=now, end=now),
        TimelineEntryObj(group=ChartEventType.MOUSE, start=now, end=now)
    ]

    for event in events:
        db_session.add(event)

    db_session.commit()

    # Refresh all events to get their computed columns
    for event in events:
        db_session.refresh(event)

    # Verify all clientFacingIds are unique
    client_facing_ids = [event.clientFacingId for event in events]
    assert len(client_facing_ids) == len(set(client_facing_ids))

    # Verify correct prefixes based on group
    assert all(
        event.clientFacingId.startswith("mouse-") for event in events if event.group == ChartEventType.MOUSE
    )
    assert all(
        event.clientFacingId.startswith("keyboard-") for event in events if event.group == ChartEventType.KEYBOARD
    )
    some_ids = [int(event.clientFacingId.split("-")[1]) for event in events]

    assert all(isinstance(x, int) for x in some_ids)


def test_timeline_entry_timestamps(db_session):
    """Test that start and end timestamps are properly stored."""
    start_time = datetime(2024, 1, 1, 12, 0)
    end_time = datetime(2024, 1, 1, 13, 0)

    event = TimelineEntryObj(
        group=ChartEventType.MOUSE,
        start=start_time,
        end=end_time
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.start == start_time
    assert event.end == end_time


# Add this to your conftest.py if you want to configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)
