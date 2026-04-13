# server.py
import os
import sys
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import asyncio

from typing import Optional

from activitytracker.db.database import (
    async_session_maker,
    init_db,
    regular_session_maker,
)
from activitytracker.features.charts_showcase.routes import router as charts_showcase_router
from activitytracker.facade.facade_singletons import (
    get_keyboard_facade_instance,
    get_mouse_facade_instance,
)
from activitytracker.facade.receive_messages import MessageReceiver
from activitytracker.routes.capture_routes import router as capture_router
from activitytracker.routes.chrome_routes import router as chrome_router
from activitytracker.routes.dashboard_legacy_routes import router as dashboard_legacy_router
from activitytracker.routes.report_routes import router as report_router
from activitytracker.routes.video_routes import router as video_router
from activitytracker.service_dependencies import (
    get_activity_arbiter,
    get_chrome_service,
)
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger

# from activitytracker.facade.program_facade import ProgramApiFacadeCore


# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)
print("SERVER STARTING WITH UNBUFFERED OUTPUT")

logger = ConsoleLogger()


# Main class in this file
class ActivityTrackerState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None


activity_tracker_state = ActivityTrackerState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    await init_db()

    # If you need to note when the computer starts up,
    # consider that the server will likely auto-run on startup
    # when it gets past development and onto being a typical daily use

    chrome_service = await get_chrome_service()
    arbiter, system_status_dao = await get_activity_arbiter()

    user_facing_clock = UserFacingClock()

    def choose_program_facade(os):
        if os.is_windows:
            from activitytracker.facade.program_facade_windows import (
                WindowsProgramFacadeCore,
            )

            return WindowsProgramFacadeCore()
        else:
            from activitytracker.facade.program_facade_ubuntu import (
                UbuntuProgramFacadeCore,
            )

            return UbuntuProgramFacadeCore()

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade
    )

    message_receiver = MessageReceiver("tcp://127.0.0.1:5555")
    activity_tracker_state.manager = SurveillanceManager(
        user_facing_clock,
        async_session_maker,
        regular_session_maker,
        chrome_service,
        arbiter,
        facades,
        message_receiver,
        system_status_dao,
    )
    activity_tracker_state.manager.print_sys_status_info()
    activity_tracker_state.manager.start_trackers()

    try:
        yield
    finally:
        # Shutdown
        activity_tracker_state.is_running = False

        print("Shutting down productivity tracking...")
        if activity_tracker_state.manager:
            try:
                # Use a timeout to ensure cleanup doesn't hang
                cancelled_count = await asyncio.wait_for(
                    activity_tracker_state.manager.cleanup(), timeout=5.0
                )
                print(f"Cleanup complete. Total tasks cancelled: {cancelled_count}")

                # Also ensure the shutdown handler runs
                activity_tracker_state.manager.shutdown_handler()
            except asyncio.CancelledError as ce:
                print(
                    "Cleanup itself was cancelled - this is likely from the web server shutting down"
                )
                # Still try to run the shutdown handler
                try:
                    activity_tracker_state.manager.shutdown_handler()
                except Exception:
                    pass
            except asyncio.TimeoutError:
                print("Cleanup timed out, forcing shutdown")
            except Exception as e:
                print(f"Error during cleanup: {e}")
                import traceback

                traceback.print_exc()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(video_router)
app.include_router(charts_showcase_router)
app.include_router(chrome_router)
app.include_router(capture_router)
app.include_router(dashboard_legacy_router)


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    logger.log_purple("[LOG] health check")
    try:
        if (
            not activity_tracker_state
            and not activity_tracker_state.manager.keyboard_tracker
        ):
            return {"status": "error", "detail": "Tracker not initialized"}
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # print("VALIDATION ERROR:", exc.errors())
    path = request.url.path
    simplified_errors = []
    for error in exc.errors():
        simplified_errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"] if loc != "body"),
                "issue": error["msg"],
            }
        )
    print(f"Validation error on {path}:")
    for error in simplified_errors:
        print(error)

    # You can also include this info in the response if desired
    return JSONResponse(
        status_code=422,
        content={"endpoint": path, "errors": simplified_errors},
    )


# TODO: Endpoint for the Camera stuff


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
