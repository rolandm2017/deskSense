import asyncio

import pytest

from activitytracker.util.task_registry import TaskRegistry


@pytest.mark.asyncio
async def test_create_task_is_tracked():
    registry = TaskRegistry(asyncio.get_event_loop())

    async def noop():
        await asyncio.sleep(0)

    task = registry.create_task(noop(), name="noop")
    assert task in registry.tasks
    await task


@pytest.mark.asyncio
async def test_cancel_all_cancels_pending_and_returns_count():
    registry = TaskRegistry(asyncio.get_event_loop())

    async def slow():
        await asyncio.sleep(10)

    registry.create_task(slow(), name="slow-1")
    registry.create_task(slow(), name="slow-2")

    cancelled = await registry.cancel_all(timeout=1.0)

    assert cancelled == 2
    assert all(t.done() for t in registry.tasks)


@pytest.mark.asyncio
async def test_cancel_all_skips_already_completed_tasks():
    registry = TaskRegistry(asyncio.get_event_loop())

    async def quick():
        return "done"

    task = registry.create_task(quick(), name="quick")
    await task
    assert task.done()

    cancelled = await registry.cancel_all(timeout=1.0)

    assert cancelled == 0


@pytest.mark.asyncio
async def test_completed_tasks_are_removed_from_registry():
    registry = TaskRegistry(asyncio.get_event_loop())

    async def quick():
        return "done"

    task = registry.create_task(quick(), name="quick")
    await task
    await asyncio.sleep(0)

    assert registry.tasks == []


@pytest.mark.asyncio
async def test_cancel_all_returns_within_timeout_for_stubborn_task():
    registry = TaskRegistry(asyncio.get_event_loop())

    async def stubborn():
        while True:
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                # Swallow cancellation; re-loop. Simulates a task that refuses
                # to yield to cancellation promptly.
                await asyncio.sleep(0.2)

    registry.create_task(stubborn(), name="stubborn")

    loop = asyncio.get_event_loop()
    started = loop.time()
    cancelled = await registry.cancel_all(timeout=0.3)
    elapsed = loop.time() - started

    assert elapsed < 1.0
    assert cancelled == 1
