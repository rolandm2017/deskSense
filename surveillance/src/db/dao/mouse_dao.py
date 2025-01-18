from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
import datetime

from ..models import MouseMove
from ..database import AsyncSession
from ...trackers.mouse_tracker import MouseMoveWindow
from ...console_logger import ConsoleLogger


class MouseMoveDto:
    def __init__(self, id, start_time, end_time):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class MouseDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.queue = Queue()
        self.logger = ConsoleLogger()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processing = False

    async def create_from_start_end_times(self, start_time: datetime, end_time: datetime):
        await self.queue.put((start_time, end_time))
        self.logger.log_blue_multiple("[LOG]" + get_rid_of_ms(start_time) + " :: " + get_rid_of_ms(end_time))
        if not self.processing:
            self.processing = True
            asyncio.create_task(self.process_queue())

    async def create_from_window(self, window: MouseMoveWindow):
        await self.queue.put((window.start_time, window.end_time))
        self.logger.log_blue("[LOG] " + get_rid_of_ms(window))
        if not self.processing:
            self.processing = True
            asyncio.create_task(self.process_queue())


    async def create_without_queue(self, start_time: datetime, end_time: datetime):
        # print("creating mouse move event", start_time)
        new_mouse_move = MouseMove(
            start_time=start_time,
            end_time=end_time
        )
        
        self.db.add(new_mouse_move)
        await self.db.commit()
        await self.db.refresh(new_mouse_move)
        return new_mouse_move

    async def read(self, mouse_move_id: int = None):
        """
        Read MouseMove entries. If mouse_move_id is provided, return specific movement,
        otherwise return all movements.
        """
        if mouse_move_id:
            return await self.db.get(MouseMove, mouse_move_id)
        
        result = await self.db.execute(select(MouseMove))
        return result.scalars().all()
    
    async def read_past_24h_events(self):
        """
        Read mouse movement events that ended within the past 24 hours.
        Returns all movements ordered by their end time.
        """
        query = select(MouseMove).where(
            MouseMove.end_time >= datetime.datetime.now() - datetime.timedelta(days=1)
        ).order_by(MouseMove.end_time.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete(self, mouse_move_id: int):
        """Delete a MouseMove entry by ID"""
        mouse_move = await self.db.get(MouseMove, mouse_move_id)
        if mouse_move:
            await self.db.delete(mouse_move)
            await self.db.commit()
        return mouse_move


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
                        
                    start_time, end_time = await self.queue.get()
                    # FIXME: what if it's a MouseMoveWindow?
                    batch.append(MouseMove(start_time=start_time, end_time=end_time))
                    
                if batch:
                    await self._save_batch(batch)
                    
            except Exception as e:
                print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        async with self.db.begin():
            self.db.add_all(batch)