from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import Program
from ...object.classes import ProgramSessionData
from ...util.console_logger import ConsoleLogger


class ProgramDao(BaseQueueingDao):
    def __init__(self, clock, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)

        self.system_clock = clock
        self.logger = ConsoleLogger()

    async def create(self, session: ProgramSessionData):
        # self.logger.log_blue("[LOG] Program event: " + session['window'])
        # Example:
        # NOTE: now has a 'window' and 'detail' field
        #  'start_time': self.start_time.isoformat(),
        # 'end_time': end_time.isoformat(),
        # 'duration': duration,
        # 'window': window_name,
        # 'detail': the_junk_string,
        # 'productive': is_productive
        duration = session.end_time - session.start_time

        program_deliverable = Program(
            window=session.window_title,
            detail=session.detail,
            start_time=session.start_time,
            end_time=session.end_time,
            duration=duration,
            productive=session.productive
        )

        await self.queue_item(program_deliverable)

    async def create_without_queue(self, session: ProgramSessionData):  # TODO: Remove
        if isinstance(session, dict):
            print("creating program row", session['start_time'])
            new_program = Program(
                window=session['window'],
                start_time=datetime.fromisoformat(session['start_time']),
                end_time=datetime.fromisoformat(session['end_time']),
                productive=session['productive']
            )

            # FIXME: this won't work with a session
            await self.db.add(new_program)
            await self.db.commit()
            await self.db.refresh(new_program)
            return new_program
        return None

    async def read_by_id(self, program_id: int):
        """
        Read Program entries. If program_id is provided, return specific program,
        otherwise return all programs.
        """
        async with self.session_maker() as session:
            return await session.get(Program, program_id)

    async def read_all(self):
        """
        Read Program entries. If program_id is provided, return specific program,
        otherwise return all programs.
        """
        async with self.session_maker() as session:
            result = await session.execute(select(Program))
            return result.scalars().all()  # TODO: return Dtos

    async def read_past_24h_events(self):
        """
        Read program activity events that ended within the past 24 hours.
        Returns all program sessions ordered by their end time.
        """
        query = select(Program).where(
            Program.end_time >= self.system_clock.now() - timedelta(days=1)
        ).order_by(Program.end_time.desc())
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()  # TODO: return Dtos

    async def delete(self, program_id: int):
        """Delete a Program entry by ID"""
        async with self.session_maker() as session:
            program = await session.get(Program, program_id)
            if program:
                await session.delete(program)
                await session.commit()
            return program
