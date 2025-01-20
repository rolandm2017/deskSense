# base_dao.py
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
import traceback


class BaseQueueingDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False

    async def queue_item(self, item, expected_type=None):
        """Common method to queue items and start processing if needed"""
        if expected_type and not isinstance(item, expected_type):
            raise ValueError("Mismatch found")
        await self.queue.put(item)
        if not self.processing:
            self.processing = True
            asyncio.create_task(self.process_queue())

    async def process_queue(self):
        """Generic queue processing logic"""
        while True:
            batch = []
            try:
                while len(batch) < self.batch_size:
                    if self.queue.empty():
                        if batch:
                            await self._save_batch(batch)
                        await asyncio.sleep(self.flush_interval)
                        continue

                    item = await self.queue.get()
                    batch.append(item)

                if batch:
                    await self._save_batch(batch)

            except Exception as e:
                traceback.print_exc()

                print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        """Save a batch of items to the database"""
        async with self.db.begin():
            self.db.add_all(batch)
