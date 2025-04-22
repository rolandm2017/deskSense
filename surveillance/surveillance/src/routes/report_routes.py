from fastapi import APIRouter, HTTPException, Depends
from typing import List

from surveillance.src.object.pydantic_dto import (
    KeyboardReport,
    MouseReport,
    ProgramActivityReport
)

from surveillance.src.services.services import (
    KeyboardService, MouseService
)

from surveillance.src.service_dependencies import (
    get_keyboard_service, get_mouse_service, get_chrome_service
)

from surveillance.src.util.pydantic_factory import (
    make_keyboard_log, make_mouse_log, make_program_log
)

from surveillance.src.util.console_logger import ConsoleLogger

# Create a logger
logger = ConsoleLogger()

# Create a router
router = APIRouter(prefix="/report", tags=["reports"])


@router.get("/keyboard/all", response_model=KeyboardReport)
async def get_all_keyboard_reports(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] keyboard report - all")
    events = await keyboard_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate keyboard report")

    logs = [make_keyboard_log(e) for e in events]
    return KeyboardReport(count=len(events), keyboardLogs=logs)


@router.get("/keyboard", response_model=KeyboardReport)
async def get_keyboard_report(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] keyboard report")
    events = await keyboard_service.get_past_days_events()

    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate keyboard report")

    logs = [make_keyboard_log(e) for e in events]
    return KeyboardReport(count=len(events), keyboardLogs=logs)


@router.get("/mouse/all", response_model=MouseReport)
async def get_all_mouse_reports(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report - all")
    events = await mouse_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate mouse report")

    reports = [make_mouse_log(e) for e in events]
    return MouseReport(count=len(reports), mouseLogs=reports)


@router.get("/mouse", response_model=MouseReport)
async def get_mouse_report(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report")
    events = await mouse_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate mouse report")

    reports = [make_mouse_log(e) for e in events]
    return MouseReport(count=len(reports), mouseLogs=reports)


# @router.get("/program/all", response_model=ProgramActivityReport)
# async def get_all_program_reports(program_service: ProgramService = Depends(get_program_service)):
#     events = await program_service.get_all_events()
#     if not isinstance(events, list):
#         raise HTTPException(
#             status_code=500, detail="Failed to generate program report")

#     reports = [make_program_log(e) for e in events]
#     return ProgramActivityReport(count=len(reports), programLogs=reports)


# @router.get("/program", response_model=ProgramActivityReport)
# async def get_program_activity_report(program_service: ProgramService = Depends(get_program_service)):
#     events = await program_service.get_past_days_events()
#     if not isinstance(events, list):
#         raise HTTPException(
#             status_code=500, detail="Failed to generate program report")

#     reports = [make_program_log(e) for e in events]
#     return ProgramActivityReport(count=len(reports), programLogs=reports)


@router.get("/chrome")
async def get_chrome_report(chrome_service=Depends(get_chrome_service)):
    logger.log_purple("[LOG] Get chrome tabs")
    reports = await chrome_service.read_last_24_hrs()
    return reports
