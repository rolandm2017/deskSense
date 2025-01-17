# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from contextlib import asynccontextmanager
import asyncio
# import time
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from pydantic import BaseModel

from src.services import MouseService, KeyboardService, ProgramService
from src.db.database import get_db, init_db, AsyncSessionLocal, AsyncSession
from src.db.dao.mouse_dao import MouseDao
from src.db.dao.keyboard_dao import KeyboardDao
from src.db.dao.program_dao import ProgramDao
from src.db.models import Keystroke, MouseMove, Program
from src.surveillance_manager import SurveillanceManager

# Add these dependency functions at the top of your file
async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    return KeyboardService(KeyboardDao(db))

async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    return MouseService(MouseDao(db))

async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    return ProgramService(ProgramDao(db))

class KeyboardLog(BaseModel):
    keyboard_event_id: int
    timestamp: datetime

class KeyboardReport(BaseModel):
    count: int
    keyboard_logs: List[KeyboardLog]

class MouseLog(BaseModel):
    mouse_event_id: int
    start_time: datetime
    end_time: datetime

class MouseReport(BaseModel):
    count: int
    mouse_reports: List[MouseLog]

class ProgramActivityLog(BaseModel):
    program_event_id: int
    window: str
    start_time: datetime
    end_time: datetime
    productive: bool

class ProgramActivityReport(BaseModel):
    count: int
    program_reports: List[ProgramActivityLog]


class SurveillanceState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None

surveillance_state = SurveillanceState()

def track_productivity():
    while surveillance_state.is_running:
        surveillance_state.manager.program_tracker.track_window()        

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    print("Starting up...")
  
    surveillance_state.db_session = AsyncSessionLocal()
    await init_db()
    
    print("Starting productivity tracking...")
    surveillance_state.manager = SurveillanceManager(surveillance_state.db_session, shutdown_signal="TODO")
    surveillance_state.is_running = True
        
    yield
    
    # Shutdown
    surveillance_state.is_running = False

    print("Shutting down productivity tracking...")
    # surveillance_state.tracking_task.cancel()
    if surveillance_state.manager:
        surveillance_state.manager.cleanup()
        # time.sleep(2)


app = FastAPI(lifespan=lifespan)


def make_keyboard_log(r: Keystroke):
    return KeyboardLog(keyboard_event_id=r.id, timestamp=r.timestamp)

def make_mouse_report(r: MouseMove):
    return MouseLog(mouse_event_id=r.id, start_time=r.start_time, end_time=r.end_time)

def make_program_report(r: Program):
    return ProgramActivityLog(
        program_event_id=r.id,
        window=r.window,
        start_time=r.start_time,
        end_time=r.end_time,
        productive=r.productive
    )

@app.get("/report/keyboard/all", response_model=KeyboardReport)
async def get_all_keyboard_reports(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await keyboard_service.get_all_events()
    print(len(events), '127ru')
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate keyboard report")
    
    logs= [make_keyboard_log(e) for e in events]  # FIXME: reports -> logs
    print(type(logs), type(logs[1]))
    return KeyboardReport(count=len(events), keyboard_logs=logs)

@app.get("/report/keyboard", response_model=KeyboardReport)
async def get_keyboard_report(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
# async def get_keyboard_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await keyboard_service.get_past_days_events()
    
    print(events, '99vm')
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate keyboard report")
    
    logs = [make_keyboard_log(e) for e in events]
    return KeyboardReport(count=len(events), keyboard_logs=logs)

@app.get("/report/mouse/all", response_model=MouseReport)
async def get_all_mouse_reports(mouse_service: MouseService = Depends(get_mouse_service)):
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await mouse_service.get_all_events()
    print(len(events), '116vm')
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    
    reports = [make_mouse_report(e) for e in events]
    return MouseReport(count=len(reports), mouse_reports=reports)
    

@app.get("/report/mouse", response_model=MouseReport)
async def get_mouse_report(mouse_service: MouseService = Depends(get_mouse_service)):
# async def get_mouse_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await mouse_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    print(len(events), '173vm')
    reports = [make_mouse_report(e) for e in events]
    print(len(reports), '175vm')
    return MouseReport(count=len(reports), mouse_reports=reports)
   

@app.get("/report/program/all", response_model=ProgramActivityReport)
async def get_all_program_reports(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await program_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate program report")
    print(events, '135vm')
    reports = [make_program_report(e) for e in events]
    return ProgramActivityReport(count=1, program_reports=reports)

@app.get("/report/program", response_model=ProgramActivityReport)
async def get_program_activity_report(program_service: ProgramService = Depends(get_program_service)):
# async def get_productivity_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await program_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate program report")
    # print(event, '135vm')
    # report_obj = ProgramActivityReport(
    #     date=event['date'],
    #     productive_time=event['productive_time'],
    #     unproductive_time=event['unproductive_time'],
    #     productive_percentage=event['productive_percentage']
    # )
    reports = [make_program_report(e) for e in events]
    return ProgramActivityReport(count=1, program_reports=reports)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
