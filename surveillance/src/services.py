from fastapi import Depends
from typing import List
from datetime import datetime

from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.mouse_dao import MouseDao
from .db.models import Keystroke, Program, MouseMove
from .db.database import get_db, AsyncSession



class KeyboardService:
    def __init__(self, dao: KeyboardDao = Depends()):
        self.dao = dao
    
    async def get_past_days_events(self) -> List[Keystroke]:
        """
        Returns all keystroke events from the last 24 hours.
        Each keystroke contains a timestamp.
        """
        events = await self.dao.read_past_24h_events()
        return events
    
    async def get_all_events(self) -> List[Keystroke]:
        """Mostly for debugging"""
        return self.dao.read()

class MouseService:
    def __init__(self, dao: MouseDao = Depends()):
        self.dao = dao
    
    async def get_past_days_events(self) -> List[MouseMove]:
        """
        Returns all mouse movements that ended in the last 24 hours.
        Each movement contains start_time and end_time.
        """
        events = await self.dao.read_past_24h_events()
        return events
    
    async def get_all_events(self) -> List[MouseMove]:
        """Mostly for debugging"""
        all = await self.dao.read()
        print(all, "in mouse.get_all_events")
        return all
    
  

class ProgramService:
    def __init__(self, dao: ProgramDao = Depends()):
        self.dao = dao
    
    async def get_past_days_events(self) -> List[Program]:
        """
        Returns all program sessions that ended in the last 24 hours.
        Each program session contains window name, start_time, end_time, 
        and productive flag.
        """
        events = await self.dao.read_past_24h_events()
        print(events, '48vm')
        return events
    
    async def get_all_events(self) -> List[Program]:
        """Mostly for debugging"""
        print(self.dao, '63vm')
        all = await self.dao.read()
        print(all, "in programs.get_all_events")
        return all
    
    
# Service dependencies
async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    dao = ProgramDao(db)
    return ProgramService(dao)

async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    dao = MouseDao(db)
    return MouseService(dao)

async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    dao = KeyboardDao(db)
    return KeyboardService(dao)
