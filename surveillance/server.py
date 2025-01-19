# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
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
from src.db.models import TypingSession, MouseMove, Program
from src.surveillance_manager import SurveillanceManager
from src.console_logger import ConsoleLogger


logger = ConsoleLogger()

# Add these dependency functions at the top of your file
async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    return KeyboardService(KeyboardDao(db))

async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    return MouseService(MouseDao(db))

async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    return ProgramService(ProgramDao(db))


class KeyboardLog(BaseModel):
    keyboard_event_id: Optional[int] = None
    timestamp: datetime

class KeyboardReport(BaseModel):
    count: int
    keyboard_logs: List[KeyboardLog]

class MouseLog(BaseModel):
    mouse_event_id: Optional[int] = None
    start_time: datetime
    end_time: datetime

class MouseReport(BaseModel):
    count: int
    mouse_reports: List[MouseLog]

class ProgramActivityLog(BaseModel):
    program_event_id: Optional[int] = None
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
        # surveillance_state.manager.program_tracker.track_window()        
        surveillance_state.manager.program_tracker.attach_listener()        

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    print("Starting up...")
  
    surveillance_state.db_session = AsyncSessionLocal()
    await init_db()
    
    print("Starting productivity tracking...")
    surveillance_state.manager = SurveillanceManager(surveillance_state.db_session, shutdown_signal="TODO")
    surveillance_state.manager.start_trackers()
        
    yield
    
    # Shutdown
    surveillance_state.is_running = False

    print("Shutting down productivity tracking...")
    # surveillance_state.tracking_task.cancel()
    if surveillance_state.manager:
        surveillance_state.manager.cleanup()
        # time.sleep(2)


app = FastAPI(lifespan=lifespan, root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_keyboard_log(r: TypingSession):
    if not hasattr(r, "timestamp"):
        raise AttributeError("Timestamp field not found")
    try:
        return KeyboardLog(
            keyboard_event_id=r.id if hasattr(r, 'id') else None,
            timestamp=r.timestamp
        )
    except AttributeError as e:
        print(r, '107ru')
        raise e

def make_mouse_report(r: MouseMove):
    try:
        return MouseLog(
            mouse_event_id=r.id if hasattr(r, 'id') else None,
            start_time=r.start_time,
            end_time=r.end_time
        )
    except AttributeError as e:
        raise e

def make_program_report(r: Program):
    try:
        return ProgramActivityLog(
            program_event_id=r.id if hasattr(r, 'id') else None,
            window=r.window,
            start_time=r.start_time,
            end_time=r.end_time,
            productive=r.productive
        )
    except AttributeError as e:
        raise e

@app.get("/report/keyboard/all", response_model=KeyboardReport)
async def get_all_keyboard_reports(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] keyboard report - all")
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
    logger.log_purple("[LOG] keyboard report")
    print(surveillance_state, surveillance_state.manager, '166ru')
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await keyboard_service.get_past_days_events()
    print(type(events), len(events), "this prints 171ru")
    
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate keyboard report")
    
    logs = [make_keyboard_log(e) for e in events]
    return KeyboardReport(count=len(events), keyboard_logs=logs)

@app.get("/report/mouse/all", response_model=MouseReport)
async def get_all_mouse_reports(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report - all")
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await mouse_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    
    reports = [make_mouse_report(e) for e in events]
    return MouseReport(count=len(reports), mouse_reports=reports)
    

@app.get("/report/mouse", response_model=MouseReport)
async def get_mouse_report(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report")
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await mouse_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")

    reports = [make_mouse_report(e) for e in events]
    return MouseReport(count=len(reports), mouse_reports=reports)
   

@app.get("/report/program/all", response_model=ProgramActivityReport)
async def get_all_program_reports(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await program_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate program report")

    reports = [make_program_report(e) for e in events]
    return ProgramActivityReport(count=len(reports), program_reports=reports)

@app.get("/report/program", response_model=ProgramActivityReport)
async def get_program_activity_report(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    events = await program_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Failed to generate program report")

    reports = [make_program_report(e) for e in events]
    return ProgramActivityReport(count=len(reports), program_reports=reports)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
