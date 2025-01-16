
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.orm import sessionmaker

import datetime

from ..models import Keystroke
from ..database import AsyncSession, get_db

class KeyboardDao:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event_time: datetime):
        print("adding keystroke ", event_time)
        new_keystroke = Keystroke(
            timestamp=event_time
        )
        
        self.db.add(new_keystroke)
        await self.db.commit()
        await self.db.refresh(new_keystroke)
        return new_keystroke

    async def read(self, keystroke_id: int = None):
        """
        Read Keystroke entries. If keystroke_id is provided, return specific keystroke,
        otherwise return all keystrokes.
        """
        if keystroke_id:
            return await self.db.get(Keystroke, keystroke_id)
        
        result = await self.db.execute(select(Keystroke))
        return result.scalars().all()

    async def delete(self,keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await self.db.get(Keystroke, keystroke_id)
        if keystroke:
            await self.db.delete(keystroke)
            await self.db.commit()
        return keystroke
    
async def example_usage():
    keyboard_dao = KeyboardDao()
    
    async for db in get_db():
        # Create example
        new_keystroke = await keyboard_dao.create(db, datetime.now())
        
        # Read example
        all_keystrokes = await keyboard_dao.read(db)
        specific_keystroke = await keyboard_dao.read(db, keystroke_id=1)
        
        # Delete example
        deleted_keystroke = await keyboard_dao.delete(db, keystroke_id=1)