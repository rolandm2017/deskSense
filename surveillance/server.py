from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from contextlib import asynccontextmanager
import asyncio
import time
from typing import Optional
from sqlalchemy.orm import Session

from pydantic import BaseModel

from src.db.database import get_db, AsyncSessionLocal
from src.surveillance_manager import SurveillanceManager

class ProductivityReport(BaseModel):
    date: str
    productive_time: float
    unproductive_time: float
    productive_percentage: float

class MouseReport(BaseModel):
    total_movements: int
    avg_movement_duration: float
    total_movement_time: float

class KeyboardReport(BaseModel):
    total_inputs: int

class SurveillanceState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None

surveillance_state = SurveillanceState()

async def track_productivity():
    while surveillance_state.is_running:
        # fixme: should this really poll every second?
        print("38rm")
        surveillance_state.manager.program_tracker.track_window()
        
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    print("Starting up...")
    
    # Create a dedicated session for the SurveillanceManager
    surveillance_state.db_session = AsyncSessionLocal()
    
    print("Starting productivity tracking...")
    # Pass the session to SurveillanceManager
    surveillance_state.manager = SurveillanceManager(surveillance_state.db_session)
    surveillance_state.is_running = True
    
    # Start tracking in background
    surveillance_state.tracking_task = asyncio.create_task(track_productivity())
    
    yield
    
    # Shutdown
    print("Shutting down productivity tracking...")
    surveillance_state.is_running = False
    
    if surveillance_state.tracking_task:
        surveillance_state.tracking_task.cancel()
        try:
            await surveillance_state.tracking_task
        except asyncio.CancelledError:
            pass
    
    if surveillance_state.manager.program_tracker:
        # Log final session
        surveillance_state.manager.program_tracker.log_session()
        
        # Clean up
        surveillance_state.manager.program_tracker.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/report", response_model=ProductivityReport)
async def get_productivity_report(db: Session = Depends(get_db)):
    if not surveillance_state.tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = surveillance_state.manager.program_tracker.generate_report()
    return ProductivityReport(
        date=report['date'],
        productive_time=report['productive_time'],
        unproductive_time=report['unproductive_time'],
        productive_percentage=report['productive_percentage']
    )

@app.get("/mouse-report", response_model=MouseReport)
async def get_mouse_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = surveillance_state.manager.mouse_tracker.generate_movement_report()
    if not isinstance(report, dict):
        raise HTTPException(status_code=500, detail="Failed to generate mouse report")
    
    return MouseReport(
        total_movements=report['total_movements'],
        avg_movement_duration=report['avg_movement_duration'],
        total_movement_time=report['total_movement_time']
    )

@app.get("/keyboard-report", response_model=KeyboardReport)
async def get_keyboard_report(db: Session = Depends(get_db)):
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")
    
    report = surveillance_state.manager.keyboard_tracker.generate_keyboard_report()
    if not isinstance(report, dict):
        raise HTTPException(status_code=500, detail="Failed to generate keyboard report")
    
    return KeyboardReport(
        total_inputs=report['total_inputs']
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)