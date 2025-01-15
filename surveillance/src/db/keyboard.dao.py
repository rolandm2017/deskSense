
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.orm import sessionmaker

import datetime

from .database import Keystroke

class KeyboardDao:
    def __init__(self):
        pass

    async def create(self, db: AsyncSession, event_time: datetime):
        """
        Create a new Keystroke entry
        
        Args:
            db (AsyncSession): The database session
            event_time (datetime): When the keystroke occurred
        
        Returns:
            Keystroke: The created Keystroke instance
        """
        new_keystroke = Keystroke(
            timestamp=event_time
        )
        
        db.add(new_keystroke)
        await db.commit()
        await db.refresh(new_keystroke)
        return new_keystroke

    async def read(self, db: AsyncSession, keystroke_id: int = None):
        """
        Read Keystroke entries. If keystroke_id is provided, return specific keystroke,
        otherwise return all keystrokes.
        """
        if keystroke_id:
            return await db.get(Keystroke, keystroke_id)
        
        result = await db.execute(select(Keystroke))
        return result.scalars().all()

    async def delete(self, db: AsyncSession, keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await db.get(Keystroke, keystroke_id)
        if keystroke:
            await db.delete(keystroke)
            await db.commit()
        return keystroke