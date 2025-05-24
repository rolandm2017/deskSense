"""
Tool for looking for sessions that have extraordinarily long durations.

Five minutes is a long session, probably it's VSCode.

This script aims to find the ones that are one hour or more.

Probably those are from the computer sleeping.
"""

import pytz
from datetime import datetime, timedelta

from typing import List

from activitytracker.config.definitions import productive_apps, productive_sites
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.db.database import async_session_maker, regular_session_maker
from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    DailySummaryBase,
    DomainSummaryLog,
    ProgramSummaryLog,
    SummaryLogBase,
)
from activitytracker.object.dashboard_dto import WeeklyProgramContent
from activitytracker.object.enums import ChartEventType
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.tz_handling.time_formatting import convert_all_to_tz
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.time_wrappers import UserLocalTime

logger = ConsoleLogger()


program_logging_dao = ProgramLoggingDao(regular_session_maker)
chrome_logging_dao = ChromeLoggingDao(regular_session_maker)
program_summary_dao = ProgramSummaryDao(program_logging_dao, regular_session_maker)
chrome_summary_dao = ChromeSummaryDao(chrome_logging_dao, regular_session_maker)


def sort_by_gathering_date(events: List):
    by_date_dict = {}
    for event in events:
        gathering_date = str(event.gathering_date).split(" ")[0]
        if gathering_date in by_date_dict:
            by_date_dict[gathering_date].append(event)
        else:
            by_date_dict[gathering_date] = [event]
    return by_date_dict


def sum_chrome_summaries(chrome_sums):
    productivity = 0
    leisure = 0
    for domain in chrome_sums:
        if domain.domain_name in productive_sites:
            productivity = productivity + domain.hours_spent
        else:
            leisure = leisure + domain.hours_spent
    return productivity, leisure


def sum_program_summaries(program_sums):
    productivity = 0
    leisure = 0
    alt_tab_window_hours = []
    for program in program_sums:
        # Make sure Chrome is SKIPPED!
        if program.program_name == "Google Chrome":
            # TODO: Verify that Chrome doesn't put a session into the Arbiter.
            continue  # Don't double count
        hours_spent: float = float(program.hours_spent)  # type: ignore
        if str(program.program_name) == "Alt-tab window":
            alt_tab_window_hours.append(program.hours_spent)
            continue  # temp - skipping bugged outputs
        if program.program_name in productive_apps:
            # print("< LOG > adding " + program.program_name)
            productivity = productivity + hours_spent
        else:
            leisure = leisure + hours_spent
    return productivity, leisure, sum(alt_tab_window_hours)


def main():
    my_tz = "America/Los_Angeles"
    developer_tz = pytz.timezone(my_tz)
    earliest_plausible_hour = 7  # in PST
    latest_plausible_hour = 23  # in PST
    pst_offset = 7  # UTC is 7 hours ahead of PST
    # utc_hour = 0
    # pst_hour = (utc_hour - pst_offset) % 24
    day_start_as_utc = (earliest_plausible_hour + pst_offset) % 24
    day_end_as_utc = (latest_plausible_hour + pst_offset) % 24

    all_program_logs = program_logging_dao.read_all()
    print(my_tz)
    all_program_logs = convert_all_to_tz(all_program_logs, my_tz)
    all_chrome_logs = chrome_logging_dao.read_all()
    print(my_tz)
    all_chrome_logs = convert_all_to_tz(all_chrome_logs, my_tz)
    all_program_summaries = program_summary_dao.read_all()
    print(my_tz)
    all_program_summaries = convert_all_to_tz(all_program_summaries, my_tz)
    all_chrome_summaries = chrome_summary_dao.read_all()
    print(my_tz)
    all_chrome_summaries = convert_all_to_tz(all_chrome_summaries, my_tz)
    # --
    # --
    # -- It should all be in PST now!!!
    # --
    # --

    program_logs_dict = sort_by_gathering_date(all_program_logs)
    for key, item in program_logs_dict.items():
        print(key, "key")
    chrome_logs_dict = sort_by_gathering_date(all_chrome_logs)

    recent_n_days_to_check = 22
    # make the recent n dates
    to_check = []  # Is in reverse chronological order
    today = datetime.now()
    gathering_date_string = today.strftime("%Y-%m-%d")

    to_check.append(gathering_date_string)
    for i in range(0, recent_n_days_to_check):
        # will be made in reverse chronological order
        n_days_ago = today - timedelta(days=i)
        gathering_date_string = n_days_ago.strftime("%Y-%m-%d")
        to_check.append(gathering_date_string)

    problem_durations_table = {}
    problem_logs_count = 0

    actual_logs = []

    one_hour_in_sec = 3600

    # Go over the latest entries in
    for i in range(recent_n_days_to_check):
        gathering_date = to_check[i]
        if gathering_date not in program_logs_dict:
            continue
        relevant_logs = program_logs_dict[gathering_date]
        for log in relevant_logs:
            log: ProgramSummaryLog | DomainSummaryLog
            log.duration_in_sec
            if log.duration_in_sec > one_hour_in_sec:
                duration_as_hours = log.duration_in_sec / one_hour_in_sec
                hours_truncated = int(duration_as_hours)
                if hours_truncated in problem_durations_table:
                    problem_durations_table[hours_truncated] += 1
                else:
                    problem_durations_table[hours_truncated] = 1
                problem_logs_count += 1
                actual_logs.append(log)

    # loop over the problem durations
    print("Problem Durations Table:")
    for hour, count in problem_durations_table.items():
        print(f"Hour: {hour} - Count: {count}")

    print("Actual problem logs:")
    for log in actual_logs:
        print(log)

    program_sums_by_date = sort_by_gathering_date(all_program_summaries)
    chrome_sums_by_date = sort_by_gathering_date(all_chrome_summaries)

    hours_by_day_out = {}

    for day, sums in program_sums_by_date.items():
        prod, leisure, alt_tab = sum_program_summaries(sums)
        if day in hours_by_day_out:
            hours_by_day_out[day] += prod
            hours_by_day_out[day] += leisure + alt_tab
        else:
            hours_by_day_out[day] = prod + leisure + alt_tab

    for day, sums in chrome_sums_by_date.items():
        prod, leisure = sum_chrome_summaries(sums)
        if day in hours_by_day_out:
            hours_by_day_out[day] += prod
            hours_by_day_out[day] += leisure
        else:
            hours_by_day_out[day] = prod + leisure

    totals_index = []

    for day, total in sorted(hours_by_day_out.items()):
        print(f"day: {day}, total: {total:.3f}")
        totals_index.append(total)

    totals_index.sort()

    for v in totals_index:
        print(round(v, 3))


if __name__ == "__main__":
    main()
