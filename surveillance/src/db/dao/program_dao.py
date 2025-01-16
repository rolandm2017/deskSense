from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from ..models import Program
from ..database import AsyncSession

class ProgramDao:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: dict):
        print(session, '13vv')
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
        return result.scalars().all()

    async def delete(self, program_id: int):
        """Delete a Program entry by ID"""
        program = await self.db.get(Program, program_id)
        if program:
            await self.db.delete(program)
            await self.db.commit()
        return program
    
async def example_usage():
    async for db in get_db():
        program_dao = ProgramDao(db)
        
        # Create example
        session_data = {
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 3600,  # 1 hour in seconds
            'window': 'Visual Studio Code',
            'productive': True
        }
        new_program = await program_dao.create(session_data)
        
        # Read example
        all_programs = await program_dao.read()
        specific_program = await program_dao.read(program_id=1)
        
        # Delete example
        deleted_program = await program_dao.delete(program_id=1)