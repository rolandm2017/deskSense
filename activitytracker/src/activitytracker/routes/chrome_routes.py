from fastapi import APIRouter, Depends, HTTPException, status

from activitytracker.object.classes import TabChangeEventWithLtz
from activitytracker.object.pydantic_dto import UtcDtTabChange
from activitytracker.service_dependencies import (
    get_chrome_service,
    get_timezone_service,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.timezone_service import TimezoneService
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.endpoint_util import field_has_utc_tzinfo_else_throw


logger = ConsoleLogger()
router = APIRouter(prefix="/api/chrome", tags=["chrome-ingest"])


@router.post("/tab", status_code=status.HTTP_204_NO_CONTENT)
async def receive_chrome_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)
        user_id = 1  # temp until i have more than 1 user

        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tab_change_timezone(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's tab endpoint"
        )


@router.post("/ignored", status_code=status.HTTP_204_NO_CONTENT)
async def receive_ignored_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    # Note that this is nigh identical to the other endpoint.
    # I diverge them early assuming they will have to diverge.
    logger.log_purple("[LOG] Ignored Chrome Tab Received")
    try:
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)
        user_id = 1  # temp until i have more than 1 user

        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tab_change_timezone(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's Ignored Route"
        )
