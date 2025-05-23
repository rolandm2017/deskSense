# video_routes.py
import traceback

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from datetime import date, datetime
from datetime import time as dt_time
from datetime import timezone
from time import time

# import time
from typing import List, Optional

from activitytracker.db.database import (
    async_session_maker,
    init_db,
    regular_session_maker,
)
from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    ProgramSummaryLog,
)
from activitytracker.facade.receive_messages import MessageReceiver
from activitytracker.object.classes import (
    PlayerStateChangeEventWithLtz,
    TabChangeEventWithLtz,
)
from activitytracker.object.pydantic_dto import UtcDtTabChange, VideoEventFactory
from activitytracker.object.pydantic_video_dto import (
    NetflixPlayerChange,
    NetflixTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
)
from activitytracker.service_dependencies import (
    get_chrome_service,
    get_timezone_service,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.services.timezone_service import TimezoneService
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.endpoint_util import field_has_utc_tzinfo_else_throw
from activitytracker.util.errors import MustHaveUtcTzInfoError, VideoRouteEventTypeError
from activitytracker.util.time_wrappers import UserLocalTime

# Create a logger
logger = ConsoleLogger()

# Create a router
router = APIRouter(prefix="/api/chrome/video", tags=["video"])


# TODO: Make these endpoints be /chrome/video/netflix/new
# TODO: Make these endpoints be /chrome/video/youtube/new
# They WERE /chrome/youtube/new, /chrome/youtube/state
@router.post("/youtube/new", status_code=status.HTTP_204_NO_CONTENT)
def receive_youtube_tab_change_event(
    tab_change_event: YouTubeTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] New YouTube received")
    try:
        print(
            f"received {tab_change_event.channel} with tabTitle {tab_change_event.tabTitle}"
        )
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz

        # Convert to unified event
        unified_event = VideoEventFactory.from_youtube_tab_change(tab_change_event)

        # Convert timezone
        localized_event = timezone_service.convert_any_video_event(unified_event, user_id)
        if not isinstance(localized_event, TabChangeEventWithLtz):
            raise VideoRouteEventTypeError()

        chrome_service.tab_queue.add_to_arrival_queue(localized_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@router.post("/youtube/state", status_code=status.HTTP_204_NO_CONTENT)
def receive_youtube_player_state(
    player_change_event: YouTubePlayerChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    # TODO: Align inputs definitions in chrome/api and server.py

    logger.log_purple("[LOG] YouTube state received")
    try:
        print("State received", player_change_event.playerState)
        field_has_utc_tzinfo_else_throw(player_change_event.eventTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: player_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(player_change_event)
        # Convert to unified event
        unified_event = VideoEventFactory.from_youtube_player_change(player_change_event)

        # Convert timezone
        localized_event = timezone_service.convert_any_video_event(unified_event)
        if not isinstance(localized_event, PlayerStateChangeEventWithLtz):
            raise VideoRouteEventTypeError()

        # Send to Chrome Service
        chrome_service.log_player_state_event(localized_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@router.post("/netflix/new", status_code=status.HTTP_204_NO_CONTENT)
def receive_netflix_tab_change_event(
    tab_change_event: NetflixTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] New Netflix received")
    try:
        # TODO: Align inputs definitions in chrome/api and server.py

        print(f"received {tab_change_event.videoId}")
        print("[video routes]", tab_change_event, "tab_change_event")
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        unified_event = VideoEventFactory.from_netflix_tab_change(tab_change_event)

        # Convert timezone
        localized_event = timezone_service.convert_any_video_event(unified_event, user_id)
        if not isinstance(localized_event, TabChangeEventWithLtz):
            raise VideoRouteEventTypeError()

        chrome_service.tab_queue.add_to_arrival_queue(localized_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()

        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's Netflix endpoint"
        )


@router.post("/netflix/state", status_code=status.HTTP_204_NO_CONTENT)
def receive_netflix_player_state(
    player_change_event: NetflixPlayerChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Netflix state received")
    try:
        # TODO: Align inputs definitions in chrome/api and server.py

        print("State received", player_change_event.showName)
        print("[video routes]", player_change_event, "player_change_event")
        field_has_utc_tzinfo_else_throw(player_change_event.eventTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: player_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(player_change_event)
        unified_event = VideoEventFactory.from_netflix_player_change(player_change_event)

        # Convert timezone
        localized_event = timezone_service.convert_any_video_event(unified_event)
        if not isinstance(localized_event, PlayerStateChangeEventWithLtz):
            raise VideoRouteEventTypeError()

        # Send to Chrome Service
        chrome_service.log_player_state_event(localized_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's Netflix endpoint"
        )
