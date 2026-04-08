import pytest

import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, Mock
import psutil
import gc

from activitytracker.db.dao.base_dao import BaseQueueingDao
from activitytracker.db.models import TimelineEntryObj


class TestResourceManagement:
    @staticmethod
    async def _wait_for_event(event: asyncio.Event, timeout: float = 0.2):
        await asyncio.wait_for(event.wait(), timeout=timeout)

    @pytest_asyncio.fixture
    async def mock_session_maker(self):
        """Create a mock session maker and session for testing"""
        # Create session
        session = AsyncMock()

        # Make regular methods regular Mocks to avoid coroutine warnings
        session.add_all = Mock()
        session.close = Mock()

        # Mock only async methods with AsyncMock
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.begin = AsyncMock()

        # Create session context manager
        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = session
        session_cm.__aexit__.return_value = None

        # Create the session maker
        maker = Mock()
        maker.return_value = session_cm
        return maker, session

    @pytest_asyncio.fixture
    async def dao(self, mock_session_maker):
        """Create a DAO instance with the mock session maker"""
        maker, _ = mock_session_maker
        dao = BaseQueueingDao(maker, batch_size=5, flush_interval=0.001)
        yield dao
        await dao.cleanup()  # Ensure cleanup happens after the test

    @pytest.mark.asyncio
    async def test_queue_processing_completes(self, dao, mock_session_maker):
        """Test that queue processing completes after all items are processed"""
        _, session = mock_session_maker

        task_completed = asyncio.Event()
        original_callback = dao._task_done_callback

        def patched_callback(task):
            task_completed.set()
            original_callback(task)

        dao._task_done_callback = patched_callback

        # save_batch_mock = AsyncMock()
        # dao._save_batch_to_db = save_batch_mock

        # Create some test items
        test_items = [TimelineEntryObj() for _ in range(10)]

        # Queue the items
        for item in test_items:
            await dao.queue_item(item)

        # Verify the background task started
        assert dao._queue_task is not None
        assert dao.processing is True

        await self._wait_for_event(task_completed)

        # Assert that the task completed and processing state is correct
        assert task_completed.is_set(), "Task completion callback was not called"
        assert dao.processing is False, "Processing flag not reset after completion"
        assert dao.queue.empty(), "Queue should be empty after processing"
        assert session.add_all.called, "Items were not saved to the database"

    @pytest.mark.asyncio
    async def test_cleanup_properly_cancels_task(self, dao):
        """Test that cleanup properly cancels the ongoing task"""
        # Queue some items to start the background task
        for _ in range(5):
            await dao.queue_item(TimelineEntryObj())

        # Verify the task is running
        assert dao._queue_task is not None
        assert not dao._queue_task.done()

        # Store a reference to the task
        task = dao._queue_task

        # Call cleanup
        await dao.cleanup()

        # Verify the task was cancelled and processing stopped
        assert dao._queue_task is None, "Task reference not cleared after cleanup"
        assert not dao.processing, "Processing flag not reset after cleanup"

        # Verify the task itself was cancelled
        assert task.cancelled() or task.done(), "Task was not properly cancelled"

        # Force garbage collection
        gc.collect()
        # Note: We cannot reliably check if the task was garbage collected
        # since asyncio might keep references to completed tasks
        # Here we're just checking that the DAO no longer references it

    @pytest.mark.asyncio
    async def test_no_resource_leaks(self, dao):
        """Test that resources are properly released after processing"""
        # Record file descriptors before test
        process = psutil.Process()
        fd_before = len(process.open_files())

        # Queue some items and let them process
        for _ in range(10):
            await dao.queue_item(TimelineEntryObj())

        # Explicitly clean up
        await dao.cleanup()

        # Force garbage collection
        gc.collect()

        # Check file descriptors after cleanup
        fd_after = len(process.open_files())

        # They should be approximately the same (allowing for some system variations)
        assert (
            abs(fd_after - fd_before) <= 2
        ), f"Possible resource leak: {fd_before} FDs before, {fd_after} after"

    @pytest.mark.asyncio
    async def test_concurrent_queue_operations(self, dao):
        """Test that the queue can handle concurrent operations correctly"""
        task_completed = asyncio.Event()
        original_callback = dao._task_done_callback

        def patched_callback(task):
            task_completed.set()
            original_callback(task)

        dao._task_done_callback = patched_callback

        # Start with an item to ensure processing is happening
        await dao.queue_item(TimelineEntryObj())
        initial_task = dao._queue_task

        # Verify a task was created
        assert initial_task is not None, "No task was created"

        # Queue more items while the first batch is processing
        for _ in range(10):
            await dao.queue_item(TimelineEntryObj())

            # Verify the task wasn't recreated mid-processing
            if not task_completed.is_set() and dao._queue_task is not None:
                assert (
                    dao._queue_task is initial_task
                ), "Task was recreated during concurrent operations"

        await self._wait_for_event(task_completed)

        # Assert that processing completed successfully
        assert task_completed.is_set(), "Task completion callback was not called"
        assert dao.queue.empty(), "Queue should be empty after processing"

    @pytest.mark.asyncio
    async def test_exception_handling_in_process_queue(self, dao, mock_session_maker):
        """Test that exceptions in process_queue are properly handled"""
        _, session = mock_session_maker
        processing_attempted = asyncio.Event()
        post_error_processing_attempted = asyncio.Event()
        original_add_all = session.add_all

        # Set up session.add_all to raise an exception
        def failing_add_all(items):
            processing_attempted.set()
            raise Exception("Test exception")

        session.add_all.side_effect = failing_add_all

        # Queue an item to trigger processing
        await dao.queue_item(TimelineEntryObj())

        await self._wait_for_event(processing_attempted)
        if dao._queue_task is not None:
            await asyncio.wait_for(dao._queue_task, timeout=0.2)

        # Core assertion: The process should not be in processing state
        # after an exception occurs
        assert not dao.processing, "Processing flag should be reset after exception"

        # Task should complete (done) even with an error
        if dao._queue_task:
            assert dao._queue_task.done(), "Task should be done after exception"

        # Ensure the queue is not blocked
        # Try adding another item and make sure it doesn't hang
        def succeeding_add_all(items):
            post_error_processing_attempted.set()
            return original_add_all(items)

        session.add_all.side_effect = None  # Remove the exception for this test
        session.add_all.side_effect = succeeding_add_all

        # Reset mock to count new calls
        session.add_all.reset_mock()

        # Queue a new item
        await dao.queue_item(TimelineEntryObj())

        await self._wait_for_event(post_error_processing_attempted)
        if dao._queue_task is not None:
            await asyncio.wait_for(dao._queue_task, timeout=0.2)

        # Check that the new processing occurred
        assert (
            session.add_all.called
        ), "Should be able to process new items after an exception"

    @pytest.mark.asyncio
    async def test_aenter_aexit_context_manager(self):
        """Test that the DAO works correctly as an async context manager"""
        # Setup
        session = AsyncMock()
        session.add_all = Mock()
        session.begin = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        print(f"In test, type of session.add_all: {type(session.add_all)}")

        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = session
        session_cm.__aexit__.return_value = None

        maker = Mock()
        maker.return_value = session_cm

        # Track if cleanup was called
        cleanup_called = False

        class TestDAO(BaseQueueingDao):
            async def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True
                await super().cleanup()

        # Use the DAO in a context manager
        async with TestDAO(maker, batch_size=5, flush_interval=0.001) as dao:
            # Queue some items
            for _ in range(5):
                await dao.queue_item(TimelineEntryObj())

            # Verify processing started
            assert dao.processing is True

        # After context exit, cleanup should have been called
        print(f"In test, type of session.add_all, near the end: {type(session.add_all)}")
        assert cleanup_called, "cleanup was not called when exiting context"
