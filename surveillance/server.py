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
from src.surveillance_manager import SurveillanceManager

# Add these dependency functions at the top of your file
async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    return ProgramService(ProgramDao(db))

async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    return MouseService(MouseDao(db))

async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    return KeyboardService(KeyboardDao(db))

class ProgramActivityReport(BaseModel):
    date: str
    productive_time: float
    unproductive_time: float
    productive_percentage: float

class MouseReport(BaseModel):
    mouse_event_id: int
    start_time: datetime
    end_time: datetime
    # total_movements: int
    # avg_movement_duration: float
    # total_movement_time: float

class KeyboardReport(BaseModel):
    total_inputs: int

class SurveillanceState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None

surveillance_state = SurveillanceState()

def track_productivity():
    while surveillance_state.is_running:
        # TODO: Put the track window on a separate thread so it's not async 
        surveillance_state.manager.program_tracker.track_window()        
        # await asyncio.sleep(1)  # FIXME: should this really poll every second?

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    print("Starting up...")
  
    # Create a dedicated session for the SurveillanceManager
    surveillance_state.db_session = AsyncSessionLocal()
    await init_db()
    
    print("Starting productivity tracking...")
    # Pass the session to SurveillanceManager
    surveillance_state.manager = SurveillanceManager(surveillance_state.db_session, shutdown_signal="TODO")
    surveillance_state.is_running = True
    
    # Start tracking in background
    # surveillance_state.tracking_task = asyncio.create_task(track_productivity())
    
    yield
    
    # Shutdown
    surveillance_state.is_running = False

    print("Shutting down productivity tracking...")
    # surveillance_state.tracking_task.cancel()
    if surveillance_state.manager:
        surveillance_state.manager.cleanup()
        # time.sleep(2)


app = FastAPI(lifespan=lifespan)


@app.get("/report/keyboard", response_model=KeyboardReport)
async def get_keyboard_report(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
# async def get_keyboard_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    # reports = await keyboard_service.get_past_days_events()
    reports = {
        "total_inputs": 9
    }
    print(reports, '99vm')
    if not isinstance(reports, dict):
        raise HTTPException(status_code=500, detail="Failed to generate keyboard report")
    
    return KeyboardReport(
        total_inputs=reports['total_inputs']
    )

def make_mouse_report(r):
    return MouseReport(total_movements=)

@app.get("/report/mouse/all", response_model=List[MouseReport])
async def get_all_mouse_reports(mouse_service: MouseService = Depends(get_mouse_service)):
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    reports = await mouse_service.get_all_events()
    print(reports, '116vm')
    if not isinstance(reports, list):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    
    return [make_mouse_report(r) for r in reports]
    # return MouseReport(
    #     total_movements=report['total_movements'],
    #     avg_movement_duration=report['avg_movement_duration'],
    #     total_movement_time=report['total_movement_time']
    # )

@app.get("/report/mouse", response_model=MouseReport)
async def get_mouse_report(mouse_service: MouseService = Depends(get_mouse_service)):
# async def get_mouse_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = await mouse_service.get_past_days_events()
    if not isinstance(report, dict):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    
    return MouseReport(
        total_movements=report['total_movements'],
        avg_movement_duration=report['avg_movement_duration'],
        total_movement_time=report['total_movement_time']
    )

@app.get("/report/program/all", response_model=ProgramActivityReport)
async def get_all_program_reports(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = await program_service.get_all_events()
    print(report, '135vm')
    return ProgramActivityReport(
        date=report['date'],
        productive_time=report['productive_time'],
        unproductive_time=report['unproductive_time'],
        productive_percentage=report['productive_percentage']
    )

@app.get("/report/program", response_model=ProgramActivityReport)
async def get_program_activity_report(program_service: ProgramService = Depends(get_program_service)):
# async def get_productivity_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = await program_service.get_past_days_events()
    print(report, '135vm')
    return ProgramActivityReport(
        date=report['date'],
        productive_time=report['productive_time'],
        unproductive_time=report['unproductive_time'],
        productive_percentage=report['productive_percentage']
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
