import pytest
from unittest.mock import Mock

import asyncio

from activitytracker.util.periodic_task import AsyncPeriodicTask


class MockSystemStatusDao:
    """
    Mocking SystemStatusDao
    """

    def __init__(self):
        pass

    def run_polling_loop(self):
        pass


@pytest.mark.asyncio
async def test_periodic_task():
    mock_dao = MockSystemStatusDao()

    run_polling_loop_mock = Mock()

    mock_dao.run_polling_loop = run_polling_loop_mock

    test_sleep_interval = 0.05  # sec
    periodic_task = AsyncPeriodicTask(mock_dao, test_sleep_interval, asyncio.sleep)

    periodic_task.start()

    cycle_count = 5
    test_duration = test_sleep_interval * cycle_count
    await asyncio.sleep(test_duration)

    assert periodic_task.is_running is True

    # Assert the task is in a pending state
    assert periodic_task.current_task is not None
    assert not periodic_task.current_task.done()
    assert not periodic_task.current_task.cancelled()
    assert str(periodic_task.current_task).startswith("<Task pending")

    periodic_task.stop()

    assert periodic_task.is_running is False

    # The task is in the process of cancelling but not cancelled
    assert "cancelling" in str(periodic_task.current_task).lower()

    # wait for the task to fully cancel
    await asyncio.sleep(0.03)

    # Assert the task is in a cancelled state
    assert periodic_task.current_task.cancelled()
    assert periodic_task.current_task.done()
    assert "cancelled" in str(periodic_task.current_task).lower()

    assert run_polling_loop_mock.call_count == cycle_count
