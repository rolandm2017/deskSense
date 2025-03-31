import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import psutil
import gc
import weakref

from src.db.dao.base_dao import BaseQueueingDao
from src.db.models import TimelineEntryObj  # Assuming this is a valid model to use for testing


class TestResourceManagement:
    @pytest_asyncio.fixture
    async def mock_session_maker(self):
        """Create a mock session maker and session for testing"""
        # Create session with begin() method that returns a context manager
        session = AsyncMock()
        session.add_all = AsyncMock()
        session.close = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        
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
        dao = BaseQueueingDao(maker, batch_size=5, flush_interval=0.1)
        yield dao
        await dao.cleanup()  # Ensure cleanup happens after the test

    @pytest.mark.asyncio
    async def test_queue_processing_completes(self, dao, mock_session_maker):
        """Test that queue processing completes after all items are processed"""
        _, session = mock_session_maker
        
        # Store task completion status
        task_completed = False
        original_callback = dao._task_done_callback
        
        # Patch the task done callback to track completion
        def patched_callback(task):
            nonlocal task_completed
            task_completed = True
            original_callback(task)
            
        dao._task_done_callback = patched_callback
        
        # Create some test items
        test_items = [TimelineEntryObj() for _ in range(10)]
        
        # Queue the items
        for item in test_items:
            await dao.queue_item(item)
        
        # Verify the background task started
        assert dao._queue_task is not None
        assert dao.processing is True
        
        # Wait for the task to complete (all items processed)
        # This includes a timeout to prevent the test from hanging
        for _ in range(50):  # Try for 5 seconds maximum
            if task_completed:
                break
            await asyncio.sleep(0.1)
        
        # Assert that the task completed and processing state is correct
        assert task_completed, "Task completion callback was not called"
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
        
        # Wait for processing to complete
        await asyncio.sleep(1)  # Give it time to process
        
        # Explicitly clean up
        await dao.cleanup()
        
        # Force garbage collection
        gc.collect()
        
        # Check file descriptors after cleanup
        fd_after = len(process.open_files())
        
        # They should be approximately the same (allowing for some system variations)
        assert abs(fd_after - fd_before) <= 2, f"Possible resource leak: {fd_before} FDs before, {fd_after} after"

    @pytest.mark.asyncio
    async def test_concurrent_queue_operations(self, dao):
        """Test that the queue can handle concurrent operations correctly"""
        # Store task completion status
        task_completed = False
        original_callback = dao._task_done_callback
        
        # Patch the task done callback to track completion
        def patched_callback(task):
            nonlocal task_completed
            task_completed = True
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
            # Add a small delay to simulate concurrent operations
            await asyncio.sleep(0.05)
            
            # Verify the task wasn't recreated mid-processing
            if not task_completed and dao._queue_task is not None:
                assert dao._queue_task is initial_task, "Task was recreated during concurrent operations"
        
        # Wait for processing to complete
        for _ in range(50):  # Try for 5 seconds maximum
            if task_completed:
                break
            await asyncio.sleep(0.1)
        
        # Assert that processing completed successfully
        assert task_completed, "Task completion callback was not called"
        assert dao.queue.empty(), "Queue should be empty after processing"

    @pytest.mark.asyncio
    async def test_exception_handling_in_process_queue(self, dao, mock_session_maker):
        """Test that exceptions in process_queue are properly handled"""
        _, session = mock_session_maker
        
        # Set up session.add_all to raise an exception
        session.add_all.side_effect = Exception("Test exception")
        
        # Store exception flag
        exception_raised = False
        
        # Patch the task done callback to track exceptions
        original_callback = dao._task_done_callback
        def patched_callback(task):
            nonlocal exception_raised
            try:
                exc = task.exception()
                if exc:
                    exception_raised = True
            except (asyncio.CancelledError, asyncio.InvalidStateError):
                pass
            original_callback(task)
            
        dao._task_done_callback = patched_callback
        
        # Queue an item to trigger processing
        await dao.queue_item(TimelineEntryObj())
        
        # Wait for the exception to be handled
        for _ in range(50):  # Try for 5 seconds maximum
            if exception_raised:
                break
            await asyncio.sleep(0.1)
        
        # Assert that the exception was handled
        assert exception_raised, "Exception was not detected in the task"
        assert dao.processing is False, "Processing flag not reset after exception"
            
    @pytest.mark.asyncio
    async def test_aenter_aexit_context_manager(self):
        """Test that the DAO works correctly as an async context manager"""
        # Setup
        session = AsyncMock()
        session.begin = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        
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
        async with TestDAO(maker, batch_size=5, flush_interval=0.1) as dao:
            # Queue some items
            for _ in range(5):
                await dao.queue_item(TimelineEntryObj())
            
            # Verify processing started
            assert dao.processing is True
        
        # After context exit, cleanup should have been called
        assert cleanup_called, "cleanup was not called when exiting context"