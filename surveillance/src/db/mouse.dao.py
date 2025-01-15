
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession

import datetime

from .database import MouseMove


class MouseDao:
    def __init__(self):
        pass

    async def create(self, db: AsyncSession, start_time: datetime, end_time: datetime):
        """
        Create a new MouseMove entry
        
        Args:
            db (AsyncSession): The database session
            start_time (datetime): When the mouse movement started
            end_time (datetime): When the mouse movement ended
        
        Returns:
            MouseMove: The created MouseMove instance
        """
        new_mouse_move = MouseMove(
            start_time=start_time,
            end_time=end_time
        )
        
        db.add(new_mouse_move)
        await db.commit()
        await db.refresh(new_mouse_move)
        return new_mouse_move

    async def read(self, db: AsyncSession, mouse_move_id: int = None):
        """
        Read MouseMove entries. If mouse_move_id is provided, return specific movement,
        otherwise return all movements.
        """
        if mouse_move_id:
            return await db.get(MouseMove, mouse_move_id)
        
        result = await db.execute(select(MouseMove))
        return result.scalars().all()

    async def delete(self, db: AsyncSession, mouse_move_id: int):
        """Delete a MouseMove entry by ID"""
        mouse_move = await db.get(MouseMove, mouse_move_id)
        if mouse_move:
            await db.delete(mouse_move)
            await db.commit()
        return mouse_move
    

async def example_usage():
    mouse_dao = MouseDao()
    
    async for db in get_db():
        # Create example
        start = datetime.now()
        end = datetime.now()  # In real usage, this would be later than start
        new_movement = await mouse_dao.create(db, start, end)
        
        # Read example
        all_movements = await mouse_dao.read(db)
        specific_movement = await mouse_dao.read(db, mouse_move_id=1)
        
        # Delete example
        deleted_movement = await mouse_dao.delete(db, mouse_move_id=1)