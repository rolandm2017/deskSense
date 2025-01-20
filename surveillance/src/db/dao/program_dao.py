from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import Program
from ...object.classes import SessionData
from ...console_logger import ConsoleLogger


class ProgramDao(BaseQueueingDao):
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        super().__init__(db, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create(self, session: SessionData):
        # self.logger.log_blue("[LOG] Program event: " + session['window'])
        # Example:
        # NOTE: now has a 'window' and 'detail' field
        #  'start_time': self.start_time.isoformat(),
        # 'end_time': end_time.isoformat(),
        # 'duration': duration,
        # 'window': window_name,
        # 'detail': the_junk_string,
        # 'productive': is_productive
        if isinstance(session, dict):
            await self.queue_item(session)

    async def create_without_queue(self, session: SessionData):
        if isinstance(session, dict):
            print("creating program row", session['start_time'])
            new_program = Program(
                window=session['window'],
                start_time=datetime.fromisoformat(session['start_time']),
                end_time=datetime.fromisoformat(session['end_time']),
                productive=session['productive']
            )

            await self.db.add(new_program)
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
        return result.scalars().all()  # TODO: return Dtos

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
