
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import  AsyncSession
from asyncio import Queue
import asyncio

from datetime import datetime, timedelta


from ..models import TypingSession
from ..database import AsyncSession, get_db
from ...object.classes import KeyboardAggregateDatabaseEntryDeliverable
from ...object.dto import KeystrokeDto
from ...console_logger import ConsoleLogger

def get_rid_of_ms(time):
    return str(time).split(".")[0]

    
class KeyboardDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processing = False

        self.logger = ConsoleLogger()

    async def create(self, session: KeyboardAggregateDatabaseEntryDeliverable):
        await self.queue.put(session)
        self.logger.log_blue("[LOG] Keyboard event: " + str(session))  # event time should be just month :: date :: HH:MM:SS
        if not self.processing:
            self.processing = True
            asyncio.create_task(self.process_queue())

    async def create_without_queue(self, session: KeyboardAggregateDatabaseEntryDeliverable):
        print("adding keystroke ", str(session))
        new_session = TypingSession(
            start_time=session.session_start_time,
            end_time=session.session_end_time
        )
        
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session

    async def read(self, keystroke_id: int = None):
        """
        Read Keystroke entries. If keystroke_id is provided, return specific keystroke,
        otherwise return all keystrokes.
        """
        if keystroke_id:
            return await self.db.get(TypingSession, keystroke_id)
        
        result = await self.db.execute(select(TypingSession))
        result = result.scalars.all()
        # print(len(result), type(result[0]), result[0], "53ru")
        return [KeystrokeDto(e[0], e[1]) for e in result]
    
    async def read_past_24h_events(self):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        # Round start_time to 5-minute intervals for grouping
        timestamp_interval = func.date_trunc('hour', TypingSession.start_time) + \
                            func.floor(func.date_part('minute', TypingSession.start_time) / 5) * \
                            timedelta(minutes=5)
        
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        query = select(
            timestamp_interval.label('session_start'),
            func.count(TypingSession.id).label('session_count')
        ).where(
            TypingSession.start_time >= twenty_four_hours_ago
        ).group_by(
            timestamp_interval
        ).order_by(
            timestamp_interval.desc()
        )
        
        result = await self.db.execute(query)
        result = result.all()
        return [KeystrokeDto(e[0], e[1]) for e in result]

    async def delete(self,keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await self.db.get(TypingSession, keystroke_id)
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
                   batch.append(TypingSession(timestamp=event_time))
                   
               if batch:
                   await self._save_batch(batch)
                   
           except Exception as e:
               print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        async with self.db.begin():
            self.db.add_all(batch)