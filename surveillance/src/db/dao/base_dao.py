from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from asyncio import Queue
import asyncio
import traceback


class BaseQueueingDao:
    """
    DAO exists to provide a queue for writes.

    Events are expected to happen quite quickly for keyboard, mouse. 
    Hence writes are batched up to be written in a group.

    The point is to (a) prevent bottlenecks and (b) avoid wasted overhead resources.
    """
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        self.session_maker = session_maker
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False
        self._queue_task = None  # Store reference to the background task

    async def queue_item(self, item, expected_type=None):
        """Common method to queue items and start processing if needed"""
        if isinstance(item, dict):
            raise ValueError("Dict found")
        if expected_type and not isinstance(item, expected_type):
            raise ValueError("Mismatch found")
        await self.queue.put(item)
        if not self.processing:
            self.processing = True
            self._queue_task = asyncio.create_task(self.process_queue())  # Store the task reference

    async def process_queue(self):
        """Generic queue processing logic"""
        while self.processing:
            batch = []
            try:
                while len(batch) < self.batch_size:
                    if self.queue.empty():
                        if batch:
                            await self._save_batch_to_db(batch)
                            batch = []  # Clear the batch after saving
                        await asyncio.sleep(self.flush_interval)
                        continue

                    item = await self.queue.get()
                    batch.append(item)

                if batch:
                    await self._save_batch_to_db(batch)

            except asyncio.CancelledError:
                # Handle cancellation gracefully
                if batch:  # Save any remaining items before exiting
                    try:
                        await self._save_batch_to_db(batch)
                    except Exception as e:
                        print(f"Error saving final batch during cleanup: {e}")
                self.processing = False
                return  # Exit the task
            except Exception as e:
                traceback.print_exc()
                print(f"Error processing batch: {e}")

    async def _save_batch_to_db(self, batch):
        """Save a batch of items to the database"""
        async with self.session_maker() as session:  # Create new session for batch
            async with session.begin():
                session.add_all(batch)
                await session.commit()

    async def cleanup(self):
        """Clean up resources and cancel any background tasks."""
        # if hasattr(self, "_queued_tasks") and len(self._queued_tasks) > 0:
        #     for task in self._queued_tasks:
        #         task.cancel()
        #         try:
        #             # Wait for cancellation to complete with a timeout
        #             await asyncio.wait_for(asyncio.shield(task), timeout=0.5)
        #         except (asyncio.CancelledError, asyncio.TimeoutError):
        #             pass  # Expected exceptions during cancellation
        if hasattr(self, '_queue_task') and self._queue_task and not self._queue_task.done():
            # Cancel the background task
            self._queue_task.cancel()
            try:
                # Wait for cancellation to complete with a timeout
                await asyncio.wait_for(asyncio.shield(self._queue_task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass  # Expected exceptions during cancellation

        # Process any remaining items in the queue
        remaining_items = []
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                remaining_items.append(item)
            except asyncio.QueueEmpty:
                break

        # Save any remaining items if there are any
        if remaining_items:
            try:
                await self._save_batch_to_db(remaining_items)
            except Exception as e:
                print(f"Error saving remaining items during cleanup: {e}")

        self.processing = False
        
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