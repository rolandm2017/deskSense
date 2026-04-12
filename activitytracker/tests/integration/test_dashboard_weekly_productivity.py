from datetime import date, datetime

import pytest
import pytz

from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.db.models import DailyDomainSummary, DailyProgramSummary
from activitytracker.services.dashboard_service import DashboardService


@pytest.mark.asyncio
async def test_dashboard_weekly_productivity_uses_seeded_summary_rows(
    regular_session_maker, plain_asm
):
    program_logging = ProgramLoggingDao(regular_session_maker)
    chrome_logging = ChromeLoggingDao(regular_session_maker)
    program_summary = ProgramSummaryDao(program_logging, regular_session_maker)
    chrome_summary = ChromeSummaryDao(chrome_logging, regular_session_maker)
    timeline_dao = TimelineEntryDao(plain_asm)
    dashboard_service = DashboardService(
        timeline_dao,
        program_summary,
        program_logging,
        chrome_summary,
        chrome_logging,
    )

    local_tz = pytz.timezone("America/Los_Angeles")
    expected_day = local_tz.localize(datetime(2025, 3, 22, 0, 0, 0))
    week_start = date(2025, 3, 16)

    productive_program_hours = 1.75
    leisure_program_hours = 0.50
    productive_domain_hours = 0.80
    leisure_domain_hours = 0.35
    expected_total_hours = (
        productive_program_hours
        + leisure_program_hours
        + productive_domain_hours
        + leisure_domain_hours
    )

    program_summary.add_new_item(
        DailyProgramSummary(
            exe_path_as_id="C:/apps/Code.exe",
            process_name="Code.exe",
            program_name="Visual Studio Code",
            hours_spent=productive_program_hours,
            gathering_date=expected_day,
            gathering_date_local=expected_day.replace(tzinfo=None),
        )
    )
    program_summary.add_new_item(
        DailyProgramSummary(
            exe_path_as_id="C:/apps/Discord.exe",
            process_name="Discord.exe",
            program_name="Discord",
            hours_spent=leisure_program_hours,
            gathering_date=expected_day,
            gathering_date_local=expected_day.replace(tzinfo=None),
        )
    )
    chrome_summary.add_new_item(
        DailyDomainSummary(
            domain_name="github.com",
            hours_spent=productive_domain_hours,
            gathering_date=expected_day,
            gathering_date_local=expected_day.replace(tzinfo=None),
        )
    )
    chrome_summary.add_new_item(
        DailyDomainSummary(
            domain_name="reddit.com",
            hours_spent=leisure_domain_hours,
            gathering_date=expected_day,
            gathering_date_local=expected_day.replace(tzinfo=None),
        )
    )

    week_result = await dashboard_service.get_weekly_productivity_overview(week_start)
    target_day = next(day for day in week_result if day["day"].date() == expected_day.date())

    assert target_day["productivity"] > 0
    assert target_day["leisure"] > 0
    assert target_day["productivity"] == pytest.approx(
        productive_program_hours + productive_domain_hours, abs=1e-4
    )
    assert target_day["leisure"] == pytest.approx(
        leisure_program_hours + leisure_domain_hours, abs=1e-4
    )
    assert target_day["productivity"] + target_day["leisure"] == pytest.approx(
        expected_total_hours, abs=1e-4
    )
