
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession

import datetime

from .database import Program, AsyncSession

class ProgramDao:
    def __init__(self):
        pass

    async def create(self, db: AsyncSession, session: dict):
        """
        Create a new Program entry
        
        Args:
            db (AsyncSession): The database session
            session (dict): Dictionary containing:
                - start_time (str): ISO formatted datetime
                - end_time (str): ISO formatted datetime
                - duration (int): Duration in seconds
                - window (str): Window name
                - productive (bool): Whether the session was productive
        
        Returns:
            Program: The created Program instance
        """
        new_program = Program(
            window=session['window'],
            start_time=datetime.fromisoformat(session['start_time']),
            end_time=datetime.fromisoformat(session['end_time']),
            productive=session['productive']
        )
        
        db.add(new_program)
        await db.commit()
        await db.refresh(new_program)
        return new_program

    async def read(self, db: AsyncSession, program_id: int = None):
        """
        Read Program entries. If program_id is provided, return specific program,
        otherwise return all programs.
        """
        if program_id:
            return await db.get(Program, program_id)
        
        result = await db.execute(select(Program))
        return result.scalars().all()

    async def delete(self, db: AsyncSession, program_id: int):
        """Delete a Program entry by ID"""
        program = await db.get(Program, program_id)
        if program:
            await db.delete(program)
            await db.commit()
        return program
    
# Example usage
async def example_usage():
    program_dao = ProgramDao()
    
    async for db in get_db():
        # Create example
        session_data = {
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 3600,  # 1 hour in seconds
            'window': 'Visual Studio Code',
            'productive': True
        }
        new_program = await program_dao.create(db, session_data)
        
        # Read example
        all_programs = await program_dao.read(db)
        specific_program = await program_dao.read(db, program_id=1)
        
        # Delete example
        deleted_program = await program_dao.delete(db, program_id=1)