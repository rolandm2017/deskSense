from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
from datetime import datetime, timedelta


from ..models import Program
from ..database import AsyncSession
from ...object.dto import ProgramDto
from ...console_logger import ConsoleLogger




class ProgramDao:
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        self.db = db
        self.queue = Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processing = False

        self.logger = ConsoleLogger()

    async def create(self, session: dict):
        # self.logger.log_blue("[LOG] Program event: " + session['window'])
        # print("program dao - creating...", session['window'])  # FIXME: window is often a bunk string - clean it up
        # Example:
        # {'os': 'Ubuntu', 'pid': 2467, 'process_name': 'Xorg', 'window_title': b'program_tracker.py - deskSense - Visual Studio Code'}
        if isinstance(session, dict):
            await self.queue.put(session)
            if not self.processing:
                self.processing = True
                asyncio.create_task(self.process_queue())

    async def create_without_queue(self, session: dict):
        if isinstance(session, dict):
            print("creating program row", session['start_time'])
            new_program = Program(
                window=session['window'],
                start_time=datetime.fromisoformat(session['start_time']),
                end_time=datetime.fromisoformat(session['end_time']),
                productive=session['productive']
            )
            
            self.db.add(new_program)
            await self.db.commit()
            await self.db.refresh(new_program)
            return new_program
        return None

    async def read(self, program_id: int = None):
        """
        Read Program entries. If program_id is provided, return specific program,
        otherwise return all programs.
        """
        if program_id:
            return await self.db.get(Program, program_id)
        
        result = await self.db.execute(select(Program))
        return result.scalars().all() # TODO: return Dtos
    
    async def read_past_24h_events(self):
        """
        Read program activity events that ended within the past 24 hours.
        Returns all program sessions ordered by their end time.
        """
        query = select(Program).where(
            Program.end_time >= datetime.now() - timedelta(days=1)  # This line is fixed
        ).order_by(Program.end_time.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()  # TODO: return Dtos

    async def delete(self, program_id: int):
        """Delete a Program entry by ID"""
        program = await self.db.get(Program, program_id)
        if program:
            await self.db.delete(program)
            await self.db.commit()
        return program
    
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

                    session = await self.queue.get()
                    batch.append(Program(
                        window=session['window'],
                        start_time=datetime.fromisoformat(session['start_time']),
                        end_time=datetime.fromisoformat(session['end_time']),
                        productive=session['productive']
                    ))

                if batch:
                    await self._save_batch(batch)

            except Exception as e:
                print(f"Error processing batch: {e}")

    async def _save_batch(self, batch):
        async with self.db.begin():
            self.db.add_all(batch)