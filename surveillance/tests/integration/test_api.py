# test_api.py
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from surveillance.server import (
    app,
    KeyboardService,
    surveillance_state,
    get_keyboard_service, get_mouse_service, get_program_service
)
from surveillance.server import app, KeyboardService, MouseService, ProgramService
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
