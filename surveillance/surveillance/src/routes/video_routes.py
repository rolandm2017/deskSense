from fastapi import APIRouter, HTTPException, Depends, status
from typing import List


from surveillance.src.service_dependencies import (
    get_video_service
)


from surveillance.src.services.tiny_services import (
    VideoService
)

from surveillance.src.object.pydantic_dto import (
    VideoCreateEvent, FrameCreateEvent, VideoCreateConfirmation,

)

from surveillance.src.util.console_logger import ConsoleLogger

# Create a logger
logger = ConsoleLogger()

# Create a router
router = APIRouter(prefix="/video", tags=["video"])


@router.post("/new", response_model=VideoCreateConfirmation)
async def receive_video_info(video_create_event: VideoCreateEvent, video_service: VideoService = Depends(get_video_service)):
    logger.log_purple("[LOG] Video create event")
    try:
        video_id = await video_service.create_new_video(video_create_event)
        return VideoCreateConfirmation(video_id=video_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Video Service"
        )


@router.post("/frame", status_code=status.HTTP_204_NO_CONTENT)
async def receive_frame_info(frame_create_event: FrameCreateEvent, video_service: VideoService = Depends(get_video_service)):
    logger.log_purple("[LOG] Video create event")
    try:
        await video_service.add_frame_to_video(frame_create_event)
        return
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Video Service"
        )
