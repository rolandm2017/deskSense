from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from ..models import MouseMove
from ..database import AsyncSession

class MouseDao:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, start_time: datetime, end_time: datetime):
        """
        Create a new MouseMove entry
        
        Args:
            start_time (datetime): When the mouse movement started
            end_time (datetime): When the mouse movement ended
        
        Returns:
            MouseMove: The created MouseMove instance
        """
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

    async def delete(self, mouse_move_id: int):
        """Delete a MouseMove entry by ID"""
        mouse_move = await self.db.get(MouseMove, mouse_move_id)
        if mouse_move:
            await self.db.delete(mouse_move)
            await self.db.commit()
        return mouse_move

async def example_usage():
    async for db in get_db():
        mouse_dao = MouseDao(db)
        
        # Create example
        start = datetime.now()
        end = datetime.now()  # In real usage, this would be later than start
        new_movement = await mouse_dao.create(start, end)
        
        # Read example
        all_movements = await mouse_dao.read()
        specific_movement = await mouse_dao.read(mouse_move_id=1)
        
        # Delete example
        deleted_movement = await mouse_dao.delete(mouse_move_id=1)