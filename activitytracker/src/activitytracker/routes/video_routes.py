# server.py
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
from activitytracker.object.pydantic_dto import (
    NetflixPlayerChange,
    NetflixTabChange,
    UtcDtTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
)
from activitytracker.service_dependencies import (
    get_chrome_service,
    get_timezone_service,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.services.tiny_services import (
    CaptureSessionService,
    TimezoneService,
)
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.endpoint_util import field_has_utc_tzinfo_else_throw
from activitytracker.util.errors import MustHaveUtcTzInfoError
from activitytracker.util.time_wrappers import UserLocalTime

# Create a logger
logger = ConsoleLogger()

# Create a router
router = APIRouter(prefix="/api/chrome/video", tags=["video"])


# TODO: Make these endpoints be /chrome/video/netflix/new
# TODO: Make these endpoints be /chrome/video/youtube/new
# They WERE /chrome/youtube/new, /chrome/youtube/state
@router.post("/youtube/new", status_code=status.HTTP_204_NO_CONTENT)
async def receive_youtube_event(
    tab_change_event: YouTubeTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        print(f"received {tab_change_event.channel} with id {tab_change_event.videoId}")
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.youtube.convert_tz_for_tab_change(tab_change_event, tz_for_user)
        )
        print(updated_tab_change_event, "92ru")
        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@router.post("/youtube/state", status_code=status.HTTP_204_NO_CONTENT)
async def receive_youtube_player_state(
    tab_change_event: YouTubePlayerChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    # TODO: Align inputs definitions in chrome/api and server.py

    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        print("State received", tab_change_event.playerState)
        field_has_utc_tzinfo_else_throw(tab_change_event.eventTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)

        # TODO: One way to solve getting the YouTubeEvent into the Arbiter,
        # is to attach it to a ChromeSession, because well, it is a chrome session.
        # And then assume that the transit makes it through OK.
        updated_tab_change_event: PlayerStateChangeEventWithLtz = (
            timezone_service.youtube.convert_tz_for_state_change(
                tab_change_event, tz_for_user
            )
        )
        print(updated_tab_change_event, " in video routes 127ru")
        # FIXME: BUT, it ISN'T a tab change event. It's a PlayerStateChangeEvent

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@router.post("/netflix/new", status_code=status.HTTP_204_NO_CONTENT)
async def receive_netflix_event(
    tab_change_event: NetflixTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        # TODO: Align inputs definitions in chrome/api and server.py

        print(f"received {tab_change_event.videoId}")
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.netflix.convert_tz_for_tab_change(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()

        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's Netflix endpoint"
        )


@router.post("/netflix/state", status_code=status.HTTP_204_NO_CONTENT)
async def receive_netflix_player_state(
    tab_change_event: NetflixPlayerChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        # TODO: Align inputs definitions in chrome/api and server.py

        print("State received", tab_change_event.showName)
        field_has_utc_tzinfo_else_throw(tab_change_event.eventTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)

        # TODO: One way to solve getting the NetflixEvent into the Arbiter,
        # is to attach it to a ChromeSession, because well, it is a chrome session.
        # And then assume that the transit makes it through OK.
        updated_tab_change_event: PlayerStateChangeEventWithLtz = (
            timezone_service.netflix.convert_tz_for_state_change(
                tab_change_event, tz_for_user
            )
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )
