from fastapi import APIRouter, Depends, HTTPException

from activitytracker.service_dependencies import get_capture_service
from activitytracker.services.tiny_services import CaptureSessionService
from activitytracker.util.console_logger import ConsoleLogger


logger = ConsoleLogger()
router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.get("/start")
async def get_capture_session_start_time(
    capture_session_service: CaptureSessionService = Depends(get_capture_service),
):
    logger.log_yellow("[Capture] Getting session start time")
    try:
        capture_session_start = capture_session_service.get_capture_start()
        return {"captureSessionStartTime": capture_session_start}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="A problem occurred in get_capture_session_start_time"
        )
