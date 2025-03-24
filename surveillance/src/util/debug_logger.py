from datetime import datetime
from sqlite3 import TimestampFromTicks
from typing import List
import json

from ..db.models import DailyDomainSummary, DailyProgramSummary, DomainSummaryLog, ProgramSummaryLog
from ..object.classes import ProgramSessionData
from ..object.pydantic_dto import TabChangeEvent


def write_to_debug_log(name, hours_spent, time):
    minutes_seconds, minutes = hours_to_minutes_seconds_ms(hours_spent)

    # print("writing to debug log: " + str(minutes_seconds))
    with open("debug_logging_-_arbiter_ver.txt", "a") as f:
        if minutes >= 1:
            f.write(f"{name} - {minutes_seconds} - {time} -- {minutes}\n")
        else:
            f.write(f"{name} - {minutes_seconds} - {time}\n")


def hours_to_minutes_seconds_ms(hours):
    # Convert hours to total seconds and milliseconds
    total_seconds = hours * 3600  # 3600 seconds in an hour

    # Extract whole minutes and remaining seconds
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    # Extract milliseconds
    milliseconds = int((total_seconds % 1) * 1000)

    # Format as mm:ss:mmm
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}", minutes


def write_to_large_usage_log(session: ProgramSessionData, hours_spent, time):
    minutes_seconds, minutes = hours_to_minutes_seconds_ms(hours_spent)
    print("Writing to large usage log: " + str(minutes_seconds))
    with open("large_usage_log_-_arbiter_ver.txt", "a") as f:
        f.write(f"{str(session)} - {minutes_seconds} - {time}\n")


# TODO: Move this
def write_temp_log(event: TabChangeEvent):
    with open("events.csv", "a") as f:
        out = f"{event.tabTitle.replace(",", "::")},{event.url},{
            str(event.startTime)}"
        f.write(out)
        f.write("\n")


def get_current_day_log_name(log_date: str):
    return "session_integrity_log - " + log_date + ".txt"


def print_and_log(sessions: List[ProgramSummaryLog] | List[DomainSummaryLog], latest_shutdown_time: datetime, startup_time: datetime):
    log_identifier = startup_time.strftime("%m-%d")
    log_for_current_day = get_current_day_log_name(log_identifier)

    with open(log_for_current_day, "a") as f:
        # latest_entry = f.read
        # if latest_entry == "log_identifier: ":
        #     return
        # else:
        f.write("\n::\n::::\nlog_identifier" + ": ")
        f.write("[shutdown time] " + str(latest_shutdown_time))
        f.write("[startup at] " + str(startup_time))
        for session in sessions:
            # print(session)
            f.write(str(session))
            f.write("\n")


def latest_line_is_log_identifier(log_file):
    with open(log_file, "r") as f:
        # Read all lines and store in a list
        lines = f.readlines()

        # Get the last n lines
        last_line = lines[-1:]

        return last_line


def capture_program_data_for_tests(program, time):
    dict_str = json.dumps(program, indent=4)
    time_str = str(time)
    with open("captures_for_test_data_-_programs.txt", "a") as f:
        f.write(time_str)
        f.write("\n")
        f.write(dict_str)
        f.write("\n\n")


def capture_chrome_data_for_tests(tab_event):
    with open("captures_for_test_data_-_Chrome.txt", "a") as f:
        f.write(str(tab_event))
        f.write("\n")
