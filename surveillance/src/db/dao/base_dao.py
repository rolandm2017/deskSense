# base_dao.py
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio


class BaseQueueingDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False

    async def queue_item(self, item):
        """Common method to queue items and start processing if needed"""
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
                print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        """Save a batch of items to the database"""
        async with self.db.begin():
            self.db.add_all(batch)
