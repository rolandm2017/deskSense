from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from asyncio import Queue
import asyncio
import traceback

from ...util.errors import WayTooLongWaitError

def handle_exception(loop, context):
    # context['message'] contains the error message
    # context['exception'] (if available) contains the exception object
    msg = context.get('exception', context['message'])
    print(f"\n⚠️ Caught asyncio exception: {msg}\n")
    traceback.print_stack()
    print("Context:", context)

class BaseQueueingDao:
    """
    DAO exists to provide a queue for writes.

    Events are expected to happen quite quickly for keyboard, mouse. 
    Hence writes are batched up to be written in a group.

    The point is to (a) prevent bottlenecks and (b) avoid wasted overhead resources.
    """
    def __init__(self, session_maker: async_sessionmaker, batch_size=30, flush_interval=1):
        self.session_maker = session_maker
        self.batch_size = batch_size
        if flush_interval > 1:
            raise WayTooLongWaitError(flush_interval)
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False
        self._queue_task = None  # Store reference to the background task
        # FIXME:  RuntimeError: There is no current event loop in thread 'MainThread'.
       

    async def queue_item(self, item, expected_type=None):
        """Common method to queue items and start processing if needed"""
        if isinstance(item, dict):
            raise ValueError("Dict found")
        if expected_type and not isinstance(item, expected_type):
            raise ValueError("Mismatch found")
        await self.queue.put(item)

        no_task_running = not self._queue_task or self._queue_task.done()
        if no_task_running:
            print("47ru")
            self.processing = True
            # loop = asyncio.get_running_loop()
            # loop.set_exception_handler(handle_exception)
            self._queue_task = asyncio.create_task(self._wrapped_process_queue())  # Store the task reference
            # self._queue_task = asyncio.create_task(self.process_queue())  # Store the task reference
            self._queue_task.add_done_callback(self._task_done_callback)

    async def _wrapped_process_queue(self):
        """Wrapper for process_queue() to log unhandled exceptions."""
        try:
            await self.process_queue()
        except Exception as e:
            loop = asyncio.get_running_loop()
            loop.call_exception_handler({"message": "Unhandled exception in process_queue", "exception": e})


    async def process_queue(self):
        """Generic queue processing logic"""
        idle_count = 0  # Count idle iterations

        while idle_count < 3 and self.processing:  # Exit if idle too many times
            print("ffffffffffffffffffffffffffffffffffff 68ru")
            batch = []
            try:
                room_in_batch = len(batch) < self.batch_size
                while room_in_batch:
                    print("room in batch loop 72ru")
                    if self.queue.empty():
                        if batch:
                            await self._save_batch_to_db(batch)
                            batch = []  # Clear the batch after saving
                        idle_count += 1
                        await asyncio.sleep(self.flush_interval)
                        continue
                    else:
                        idle_count = 0  # Reset idle count on activity

                    item = await self.queue.get()
                    batch.append(item)
                    room_in_batch = len(batch) < self.batch_size

                if batch:
                    await self._save_batch_to_db(batch)

            except asyncio.CancelledError:
                # print("Task was cancelled! Stack trace:")
                # traceback.print_stack()
                # raise  # Re-raise to ensure proper cancellation handling
                # Handle cancellation gracefully
                if batch:  # Save any remaining items before exiting
                    try:
                        await self._save_batch_to_db(batch)
                    except Exception as e:
                        print(f"Error saving final batch during cleanup: {e}")
                return  # Exit the task
            except Exception as e:
                traceback.print_exc()
                print(f"Error processing batch: {e}")
        # self._queue_task = None  # Reset task reference when exiting
        self.processing = False

    def _task_done_callback(self, task):
        """Handles task completion, including unexpected completion."""
        try:
            # Check if task raised an exception
            exc = task.exception()
            if exc:
                print(f"Task raised exception: {exc}")
        except asyncio.CancelledError:
            pass  # Task was cancelled, which is normal
        
        # Ensure we reset processing state
        self.processing = False
        # Only set _queue_task to None if it's this task
        if self._queue_task == task:
            self._queue_task = None

    async def _save_batch_to_db(self, batch):
        """Save a batch of items to the database"""
        print("Opening session for batch save")
        async with self.session_maker() as session:
            # Start transaction
            async with session.begin():
                session.add_all(batch)
            print("Session context exited")
        print("Session fully closed")
                # No need to call commit explicitly as session.begin() handles it
            # Ensure connection is returned to the pool properly
        # Session is closed here
                
    async def _force_process_queue(self):
        """Force immediate processing of queued items. Can be useful for tests or shutdown"""
        # Get all items from the queue
        remaining_items = []
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                remaining_items.append(item)
            except asyncio.QueueEmpty:
                break
                
        # Save items if there are any
        if remaining_items:
            await self._save_batch_to_db(remaining_items)

    async def cleanup(self):
        """Clean up resources and cancel any background tasks."""
        self.processing = False  # break the loop
        print(self._queue_task, "fff87ru")
        if self._queue_task and not self._queue_task.done():
            # Cancel the background task
            self._queue_task.cancel()
            try:
                # Wait for cancellation to complete with a timeout
                await asyncio.wait_for(asyncio.shield(self._queue_task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass  # Expected exceptions during cancellation

        # Force drain the connection pool for this session maker
        # An aggressive approach that should clear any lingering connections
        try:
            # Create a test session and immediately close it to drain the pool
            async with self.session_maker() as session:
                pass  # Session is automatically closed when exiting context
        except Exception as e:
            print(f"Error draining connection pool: {e}")

        # Process any remaining items in the queue
        await self._force_process_queue()
        
    async def __aenter__(self):
        """Support for async context manager protocol"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup happens when using 'async with'"""
        await self.cleanup()

# NOTE from me & Claude:

# There was a leak of some kind, keeping the program running even after the OS (language?) attempted to clean everything up.
# As Claude explains:
"""
The fundamental issue is that you're creating a background task 
with asyncio.create_task() but never storing a reference to it or 
providing a way to cancel it. This task contains an 
infinite while True loop that keeps a database connection open.
"""

# # In BaseQueueingDao.__init__
# self.processing = False  # Flag that controls whether the background task is started

# # In BaseQueueingDao.queue_item
# if not self.processing:
#     self.processing = True
#     asyncio.create_task(self.process_queue())  # Creates a background task but never stores a reference to it

# # In BaseQueueingDao.process_queue
# while True:  # Infinite loop that keeps running even after test completes
#     # ... processing logic ...
#     async with self.session_maker() as session:  # Opens a DB connection that never gets closed
#         # ... database operations ...