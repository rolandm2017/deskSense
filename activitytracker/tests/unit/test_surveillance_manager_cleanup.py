from unittest.mock import AsyncMock

import pytest

from activitytracker.surveillance_manager import SurveillanceManager


@pytest.mark.asyncio
async def test_cancel_pending_tasks_cleans_up_queued_daos():
    manager = SurveillanceManager.__new__(SurveillanceManager)
    manager.is_test = True
    manager.tasks = AsyncMock()
    manager.tasks.cancel_all.return_value = 2
    manager.timeline_dao = AsyncMock()
    manager.keyboard_dao = AsyncMock()
    manager.mouse_dao = AsyncMock()

    cancelled = await manager.cancel_pending_tasks()

    assert cancelled == 2
    manager.tasks.cancel_all.assert_awaited_once_with(timeout=3.0)
    manager.timeline_dao.cleanup.assert_awaited_once()
    manager.keyboard_dao.cleanup.assert_awaited_once()
    manager.mouse_dao.cleanup.assert_awaited_once()
