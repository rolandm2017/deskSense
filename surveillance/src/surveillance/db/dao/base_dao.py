from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from asyncio import Queue
import asyncio
import traceback
import weakref

from surveillance.src.util.errors import WayTooLongWaitError


def handle_exception(loop, context):
    # context['message'] contains the error message
    # context['exception'] (if available) contains the exception object
    msg = context.get('exception', context['message'])
    task = context.get("task")
    task_name = task.get_name() if task else "Unknown-Task"
    print(f"\n⚠️ Caught asyncio exception: {msg}\nIn: {task_name}\n")
    # traceback.print_stack()
    print("Context:", context)


class BaseQueueingDao:
    """
    DAO exists to provide a queue for writes.

    Events are expected to happen quite quickly for keyboard, mouse. 
    Hence writes are batched up to be written in a group.

    The point is to (a) prevent bottlenecks and (b) avoid wasted overhead resources.
    """

    def __init__(self, async_session_maker: async_sessionmaker, batch_size=30, flush_interval: int | float = 1, dao_name="BaseQueueingDao"):
        self.async_session_maker = async_session_maker
        self.batch_size = batch_size
        if flush_interval > 1:
            raise WayTooLongWaitError(flush_interval)
        self.flush_interval = flush_interval
        self.dao_name = dao_name
        self.queue = Queue()
        self.processing = False
        self._queue_task = None  # Store reference to the background task
        # Register an exception handler for the current event loop
        try:
            loop = asyncio.get_running_loop()
            # loop.set_exception_handler(handle_exception)
        except RuntimeError:
            # No event loop, which is fine - will be set when needed
            pass

    async def queue_item(self, item, expected_type=None, source=None):
        """Common method to queue items and start processing if needed"""
        if isinstance(item, dict):
            raise ValueError("Dict found")
        if expected_type and not isinstance(item, expected_type):
            raise ValueError(
                f"Expected {expected_type.__name__}, got {type(item).__name__}")

        await self.queue.put(item)

        # Only start a new task if no task is running or the previous one is done
        no_queue_running = self._queue_task is None or self._queue_task.done()
        if no_queue_running:
            self.processing = True
            # Create a new task and store a strong reference to it
            # self._queue_task = asyncio.create_task(self._wrapped_process_queue())
            self._queue_task = asyncio.create_task(
                self._wrapped_process_queue(),
                name=f"{self.dao_name}-{source}-Task"
            )
            self._queue_task.add_done_callback(self._task_done_callback)

    async def _wrapped_process_queue(self):
        """Wrapper for process_queue() to log unhandled exceptions."""
        try:
            await self.process_queue()
        except asyncio.CancelledError:
            # Let cancellation bubble up properly
            print("_wrapped_process_queue was cancelled")
            raise
        except Exception as e:
            print(f"Exception in _wrapped_process_queue: {e}")
            # traceback.print_exc()
            # Report the exception to the event loop
            loop = asyncio.get_running_loop()
            loop.call_exception_handler({
                "message": "Unhandled exception in process_queue",
                "exception": e,
                "task": asyncio.current_task()
            })
            # Re-raise to mark the task as failed
            raise

    async def process_queue(self):
        """Generic queue processing logic"""
        idle_count = 0  # Count idle iterations

        try:
            while idle_count < 3 and self.processing:  # Exit if idle too many times
                # print(f"Processing queue (idle count: {idle_count})")
                batch = []

                # Fill batch until full or queue empty
                try:
                    while len(batch) < self.batch_size and not self.queue.empty():
                        try:
                            item = self.queue.get_nowait()
                            batch.append(item)
                            idle_count = 0  # Reset idle count on activity
                        except asyncio.QueueEmpty:
                            break

                    # Save batch if not empty
                    if batch:
                        try:
                            await self._save_batch_to_db(batch)
                            batch = []  # Clear the batch after saving
                        except Exception as e:
                            print(f"Error saving batch: {e}")
                            # traceback.print_exc()
                            # Continue with the next batch
                    else:
                        # No items in queue, increment idle count and wait
                        idle_count += 1
                        await asyncio.sleep(self.flush_interval)

                except Exception as e:
                    print(f"Unexpected error in process_queue: {e}")
                    # traceback.print_exc()
                    # Don't exit the loop on unexpected errors
                    await asyncio.sleep(self.flush_interval)

        except asyncio.CancelledError:
            print("Queue processing task was cancelled")
            # Save any remaining items before exiting if there are any
            if batch:
                try:
                    await self._save_batch_to_db(batch)
                except Exception as e:
                    print(f"Error saving final batch during cancellation: {e}")
            raise  # Re-raise to ensure proper cancellation handling

        finally:
            # print("Queue processing completed or cancelled")
            self.processing = False

    def _task_done_callback(self, task):
        """Handles task completion, including unexpected completion."""
        try:
            # Check if task raised an exception
            exc = task.exception()
            if exc:
                print(f"Task raised exception: {exc}")
        except asyncio.CancelledError:
            print("Task was cancelled, which is expected during cleanup")
        except Exception as e:
            print(f"Error checking task exception: {e}")

        # Always ensure we reset processing state
        self.processing = False

        # Only clear the queue task reference if it's this task
        if self._queue_task is task:
            self._queue_task = None

    async def _save_batch_to_db(self, batch):
        """Save a batch of items to the database"""
        # print(f"Saving batch of {len(batch)} items to database")
        try:
            async with self.async_session_maker() as session:
                # Use the manual transaction approach to avoid nesting issues
                await session.begin()
                try:
                    # print(f"Type of session.add_all: {type(session.add_all)}")
                    session.add_all(batch)
                    await session.commit()
                    # print("Batch saved successfully")
                except Exception as e:
                    await session.rollback()
                    print(f"Error during transaction, rolling back: {e}")
                    raise
        except Exception as e:
            print(f"Error in _save_batch_to_db: {e}")
            # traceback.print_exc()
            raise  # Re-raise to allow proper error handling

    async def cleanup(self):
        """Clean up resources and cancel any background tasks."""
        print("Starting cleanup...")

        # Signal processing to stop
        self.processing = False

        # Cancel any running task
        if self._queue_task and not self._queue_task.done():
            print("Cancelling running queue task")
            # Store a reference to the task before we null it out
            task = self._queue_task
            # First mark our reference as None to prevent race conditions
            self._queue_task = None

            # Then cancel the task
            task.cancel()
            try:
                # Wait for cancellation to complete with a timeout
                await asyncio.wait_for(task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                print("Task cancellation completed or timed out")
            except Exception as e:
                print(f"Unexpected error during task cancellation: {e}")

        # Process any remaining items
        await self._force_process_queue()

        print("Cleanup completed")

    async def _force_process_queue(self):
        """Force immediate processing of queued items. Useful for tests or shutdown."""
        # print("Force processing remaining queue items")
        remaining_items = []

        # Empty the queue
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                remaining_items.append(item)
            except asyncio.QueueEmpty:
                break

        # Save items if there are any
        if remaining_items:
            print(f"Force saving {len(remaining_items)} remaining items")
            await self._save_batch_to_db(remaining_items)
        else:
            print("No remaining items to process")

    async def __aenter__(self):
        """Support for async context manager protocol"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup happens when using 'async with'"""
        await self.cleanup()
