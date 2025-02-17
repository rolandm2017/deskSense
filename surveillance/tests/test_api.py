# test_api.py
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from surveillance.src.services.dashboard_service import DashboardService
from surveillance.server import (
    app,
    surveillance_state,
    get_dashboard_service, get_keyboard_service, get_mouse_service, get_program_service,

)
from surveillance.server import app, KeyboardService, MouseService, ProgramService

from surveillance.src.db.models import TimelineEntryObj, ChartEventType, DailyProgramSummary
from surveillance.src.db.dao.keyboard_dao import TypingSessionDto
from surveillance.src.db.dao.mouse_dao import MouseMoveDto
from surveillance.src.db.dao.program_dao import ProgramDao

from surveillance.src.object.dto import ProgramDto


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_keyboard_events():
    base_time = datetime.now()
    events = []
    for i in range(12):  # 12, 14, 16
        event = TypingSessionDto(
            i, base_time + timedelta(minutes=i*1), base_time + timedelta(minutes=i*2))
        events.append(event)
    return events


@pytest.fixture
def mock_mouse_events():
    base_time = datetime.now()
    events = []
    for i in range(14):  # 12, 14, 16
        event = MouseMoveDto(
            i, base_time - timedelta(minutes=i*1), base_time - timedelta(minutes=i*2))
        events.append(event)
    return events


@pytest.fixture
def mock_program_events():
    base_time = datetime.now()
    events = []
    for i in range(16):  # 12, 14, 16
        event = ProgramDto(i, "Foo", "Bar - a detail", base_time +
                           timedelta(minutes=i), base_time + timedelta(minutes=i*1), i % 2 == 0)
        events.append(event)
    return events


@pytest.fixture
def mock_timeline_data():
    base_time = datetime.now()

    # Create mock mouse entries
    mouse_entries = []
    for i in range(5):
        entry = TimelineEntryObj(
            id=i,
            clientFacingId=f"mouse-{i}",
            group=ChartEventType.MOUSE,
            content=f"Mouse Event {i}",
            start=base_time + timedelta(minutes=i*10),
            end=base_time + timedelta(minutes=(i+1)*10)
        )
        mouse_entries.append(entry)

    # Create mock keyboard entries
    keyboard_entries = []
    for i in range(5):
        entry = TimelineEntryObj(
            id=i+10,
            clientFacingId=f"keyboard-{i}",
            group=ChartEventType.KEYBOARD,
            content=f"Typing Session {i}",
            start=base_time + timedelta(minutes=i*15),
            end=base_time + timedelta(minutes=(i+1)*15)
        )
        keyboard_entries.append(entry)

    return mouse_entries, keyboard_entries


@pytest.fixture
def mock_program_summary_data():
    base_time = datetime.now()
    return [
        DailyProgramSummary(
            id=1,
            program_name="Chrome",
            hours_spent=2.5,
            gathering_date=base_time
        ),
        DailyProgramSummary(
            id=2,
            program_name="VS Code",
            hours_spent=4.0,
            gathering_date=base_time
        ),
        DailyProgramSummary(
            id=3,
            program_name="Terminal",
            hours_spent=1.5,
            gathering_date=base_time
        )
    ]


@pytest.fixture
def mock_surveillance_state():
    manager_mock = MagicMock()
    manager_mock.keyboard_tracker = True  # FIXME: this doesn't even get used?
    surveillance_state.manager = manager_mock
    return manager_mock


@pytest.mark.asyncio
async def test_get_keyboard_report(test_client, mock_keyboard_events, mock_surveillance_state):
    mock_service = KeyboardService(AsyncMock())
    mock_service.get_past_days_events = AsyncMock(
        return_value=mock_keyboard_events)

    async def override_get_keyboard_service():
        return mock_service

    app.dependency_overrides[get_keyboard_service] = override_get_keyboard_service

    try:
        response = test_client.get("/report/keyboard")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 12
        assert len(data["keyboardLogs"]) == 12
        # assert 1 == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_mouse_report(test_client, mock_mouse_events, mock_surveillance_state):
    mock_service = MouseService(AsyncMock())
    mock_service.get_past_days_events = AsyncMock(
        return_value=mock_mouse_events)

    async def override_get_mouse_service():
        return mock_service

    app.dependency_overrides[get_mouse_service] = override_get_mouse_service

    try:
        response = test_client.get("/report/mouse")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 14
        assert len(data["mouseLogs"]) == 14
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_program_report(test_client, mock_program_events, mock_surveillance_state):
    mock_service = ProgramService(AsyncMock())
    mock_service.get_past_days_events = AsyncMock(
        return_value=mock_program_events)

    async def override_get_program_service():
        return mock_service

    app.dependency_overrides[get_program_service] = override_get_program_service

    try:
        response = test_client.get("/report/program")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 16
        assert len(data["programLogs"]) == 16
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_all_keyboard_reports(test_client, mock_keyboard_events, mock_surveillance_state):
    mock_service = KeyboardService(AsyncMock())
    mock_service.get_all_events = AsyncMock(return_value=mock_keyboard_events)

    async def override_get_keyboard_service():
        return mock_service

    app.dependency_overrides[get_keyboard_service] = override_get_keyboard_service

    try:
        response = test_client.get("/report/keyboard/all")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 12
        assert len(data["keyboardLogs"]) == 12
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_all_mouse_reports(test_client, mock_mouse_events, mock_surveillance_state):
    mock_service = MouseService(AsyncMock())
    mock_service.get_all_events = AsyncMock(return_value=mock_mouse_events)

    async def override_get_mouse_service():
        return mock_service

    app.dependency_overrides[get_mouse_service] = override_get_mouse_service

    try:
        response = test_client.get("/report/mouse/all")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 14
        assert len(data["mouseLogs"]) == 14
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_all_program_reports(test_client, mock_program_events, mock_surveillance_state):
    mock_service = ProgramService(AsyncMock())
    mock_service.get_all_events = AsyncMock(return_value=mock_program_events)

    async def override_get_program_service():
        return mock_service

    app.dependency_overrides[get_program_service] = override_get_program_service

    try:
        response = test_client.get("/report/program/all")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 16
        assert len(data["programLogs"]) == 16
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_timeline_for_dashboard(
    test_client,
    mock_timeline_data,
    mock_surveillance_state
):
    mouse_entries, keyboard_entries = mock_timeline_data
    mock_service = DashboardService(AsyncMock(), AsyncMock(), AsyncMock())
    mock_service.get_timeline = AsyncMock(
        return_value=(mouse_entries, keyboard_entries)
    )

    async def override_get_dashboard_service():
        return mock_service

    app.dependency_overrides[get_dashboard_service] = override_get_dashboard_service

    try:
        response = test_client.get("/dashboard/timeline")
        assert response.status_code == 200
        data = response.json()

        # Check structure and counts
        assert "mouseRows" in data
        assert "keyboardRows" in data
        assert len(data["mouseRows"]) == 5
        assert len(data["keyboardRows"]) == 5

        # Verify mouse entry structure
        mouse_entry = data["mouseRows"][0]
        assert "id" in mouse_entry
        assert "group" in mouse_entry
        assert "content" in mouse_entry
        assert "start" in mouse_entry
        assert "end" in mouse_entry
        assert mouse_entry["group"] == "mouse"

        # Verify keyboard entry structure
        keyboard_entry = data["keyboardRows"][0]
        assert keyboard_entry["group"] == "keyboard"
        assert keyboard_entry["id"].startswith("keyboard-")

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_program_time_for_dashboard(
    test_client,
    mock_program_summary_data,
    mock_surveillance_state
):
    print("305ru")
    mock_service = DashboardService(AsyncMock(), AsyncMock(), AsyncMock())
    mock_service.get_program_summary = AsyncMock(
        return_value=mock_program_summary_data
    )

    async def override_get_dashboard_service():
        return mock_service

    app.dependency_overrides[get_dashboard_service] = override_get_dashboard_service

    try:
        print("316ru")
        response = test_client.get("/dashboard/program/summaries")
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "columns" in data
        assert len(data["columns"]) == 3
        print("324ru")

        # Verify program summary entry structure
        program_entry = data["columns"][0]
        assert "id" in program_entry
        assert "programName" in program_entry
        assert "hoursSpent" in program_entry
        assert "gatheringDate" in program_entry

        # Verify specific data
        chrome_entry = next(
            entry for entry in data["columns"]
            if entry["programName"] == "Chrome"
        )
        assert chrome_entry["hoursSpent"] == 2.5

    finally:
        app.dependency_overrides.clear()
