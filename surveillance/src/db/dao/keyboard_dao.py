
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession
from asyncio import Queue
import asyncio
from datetime import datetime

from ..models import Keystroke
from ..database import AsyncSession, get_db

class KeyboardDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processing = False

    async def create(self, event_time: datetime):
        await self.queue.put(event_time)
        if not self.processing:
            self.processing = True
            asyncio.create_task(self.process_queue())

    async def create_without_queue(self, event_time: datetime):
        print("adding keystroke ", event_time)
        new_keystroke = Keystroke(
            timestamp=event_time
        )
        
        self.db.add(new_keystroke)
        await self.db.commit()
        await self.db.refresh(new_keystroke)
        return new_keystroke

    async def read(self, keystroke_id: int = None):
        """
        Read Keystroke entries. If keystroke_id is provided, return specific keystroke,
        otherwise return all keystrokes.
        """
        if keystroke_id:
            return await self.db.get(Keystroke, keystroke_id)
        
        result = await self.db.execute(select(Keystroke))
        return result.scalars().all()

    async def delete(self,keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await self.db.get(Keystroke, keystroke_id)
        if keystroke:
            await self.db.delete(keystroke)
            await self.db.commit()
        return keystroke
    
    async def process_queue(self):
       while True:
           batch = []
           try:
               while len(batch) < self.batch_size:
                   if self.queue.empty():
                       if batch:
                           await self._save_batch(batch)
                       await asyncio.sleep(self.flush_interval)
                       continue
                   
                   event_time = await self.queue.get()
                   batch.append(Keystroke(timestamp=event_time))
                   
               if batch:
                   await self._save_batch(batch)
                   
           except Exception as e:
               print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        async with self.db.begin():
            self.db.add_all(batch)