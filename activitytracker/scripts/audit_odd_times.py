"""

# --
#
# -- Tool for checking that the db contains no sessions from when the computer was not used.
#
# --

The intent is to look for days where the data surely is from a bug.

"""

from datetime import datetime, timedelta
from typing import List

import pytz

from surveillance.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.db.database import async_session_maker, regular_session_maker
from surveillance.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    DailySummaryBase,
    DomainSummaryLog,
    ProgramSummaryLog,
    SummaryLogBase,
)
from surveillance.object.dashboard_dto import WeeklyProgramContent
from surveillance.object.enums import ChartEventType
from surveillance.services.dashboard_service import DashboardService
from surveillance.util.console_logger import ConsoleLogger
from surveillance.util.const import SECONDS_PER_HOUR
from surveillance.util.time_wrappers import UserLocalTime

logger = ConsoleLogger()


program_logging_dao = ProgramLoggingDao(regular_session_maker)
chrome_logging_dao = ChromeLoggingDao(regular_session_maker)
program_summary_dao = ProgramSummaryDao(
    program_logging_dao, regular_session_maker)
chrome_summary_dao = ChromeSummaryDao(
    chrome_logging_dao, regular_session_maker)


def sort_by_gathering_date(events: List):
    by_date_dict = {}
    for event in events:
        gathering_date = str(event.gathering_date).split(" ")[0]
        if gathering_date in by_date_dict:
            by_date_dict[gathering_date].append(event)
        else:
            by_date_dict[gathering_date] = [event]
    return by_date_dict


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
    all_program_logs = convert_all_to_tz(all_program_logs, my_tz)
    # all_chrome_logs = chrome_logging_dao.read_all()
    # all_program_summaries = program_summary_dao.read_all()
    # all_chrome_summaries = chrome_summary_dao.read_all()
    # --
    # --
    # -- It should all be in PST now!!!
    # --
    # --

    program_logs_dict = sort_by_gathering_date(all_program_logs)
    # exit()
    # domain_logs_dict = sort_by_gathering_date(all_chrome_logs)
    # program_sums_dict = sort_by_gathering_date(all_program_summaries)
    # domain_sums_dict = sort_by_gathering_date(all_chrome_summaries)

    recent_n_days_to_check = 6
    # make the recent n dates
    to_check = []  # Is in reverse chronological order
    today = datetime.now()
    gathering_date_string = today.strftime("%Y-%m-%d")

    to_check.append(gathering_date_string)
    for i in range(0, recent_n_days_to_check):
        # will be made in reverse chronological order
        n_days_ago = today - timedelta(days=i)
        gathering_date_string = n_days_ago.strftime("%Y-%m-%d")
        # print(gathering_date_string, type(gathering_date_string), "128ru")
        to_check.append(gathering_date_string)

    end_times_hashtable = {}
    problem_logs = 0

    # FIXME: adjust the problem logs values by PST offset:  pst_hour = (utc_hour - pst_offset) % 24

    # FIXME: account for PST -> UTC -> PST

    # Go over the latest entries in
    for i in range(recent_n_days_to_check):
        gathering_date = to_check[i]
        # print(type(gathering_date), "137ru")
        relevant_logs = program_logs_dict[gathering_date]
        for log in relevant_logs:
            log: ProgramSummaryLog | DomainSummaryLog
            end_hour = log.end_time.hour
            if end_hour in end_times_hashtable:
                end_times_hashtable[end_hour] += 1
            else:
                end_times_hashtable[end_hour] = 1
            if end_hour > day_start_as_utc or end_hour < day_end_as_utc:

                problem_logs += 1
                # print("Problem log:", log)

    print("end times table:")
    for i in range(0, 24):
        if i in end_times_hashtable:

            print(f"{i}: {end_times_hashtable[i]}")
        else:
            print(f"{i}: 0")
    # print(f"PST end times:")
    # pst_table = {}
    # pst_offset = 7  # UTC is 7 hours ahead of PST
    # for utc_hour in range(0, 24):
    #     # Convert UTC to PST (subtract offset)
    #     pst_hour = (utc_hour - pst_offset) % 24

    #     # Map the UTC value to the PST hour
    #     if utc_hour in end_times_hashtable:
    #         pst_table[pst_hour] = end_times_hashtable[utc_hour]
    #     else:
    #         pst_table[pst_hour] = 0

    # # Print PST table in order
    # for i in range(0, 24):
    #     if i in pst_table:
    #         print(f"{i}: {pst_table[i]}")
    #     else:
    #         print(f"{i}: 0")
    # print(f"total problem logs: {problem_logs}")


#         # This is how you would run the async function
if __name__ == "__main__":
    main()

# # TODO: Go day by day for the past two weeks.
