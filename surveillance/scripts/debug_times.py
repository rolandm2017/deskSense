"""

####
#
#  Tool for inspecting tracker times for {mouse, keyboard} vs {programs, chrome}
#
####

Run the script, and see:
1. How much time was spent moving the peripherals?
2. How much time was spent total on programs/Chrome?
3. What is the ratio of programs & Chrome to peripherals?

Each by day.

The intent is to look for days where the ratio is WAY off, 
not 1.25:1 but 4:1, which is impossible.
"""

from datetime import datetime, timedelta

from surveillance.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.db.database import async_session_maker, regular_session_maker
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
timeline_entry_dao = TimelineEntryDao(async_session_maker)


dashboard_service = DashboardService(
    timeline_entry_dao, program_summary_dao, program_logging_dao, chrome_summary_dao, chrome_logging_dao)


async def get_peripherals_for_day(day):
    keyboard = await timeline_entry_dao.read_day(day, ChartEventType.KEYBOARD)
    mouse = await timeline_entry_dao.read_day(day, ChartEventType.MOUSE)
    return keyboard, mouse


def get_productivity_for_week(starting_sunday):
    return dashboard_service.get_weekly_productivity_overview(starting_sunday)


def get_productive_hours_for_day(day, weekly_productivity):
    for entry in weekly_productivity:
        if day == entry["day"]:
            return entry
    return None


def get_leisure_for_day(day):
    pass


def get_productivity_for_day(day, week_of_productivity):
    for entry in week_of_productivity:
        if day == entry["day"]:
            return entry
    return None


def sum_peripheral_hours(results_from_day):
    pass


def sum_hours_for_peripheral(day_of_peripherals):
    total = 0
    for event in day_of_peripherals:
        duration: timedelta = event.end - event.start
        total += duration.total_seconds() / 3600  # convert to hours
    return total


def hours_to_hh_mm(hours):
    """
    Convert hours as a float to hh:mm format.

    Args:
        hours (float): Number of hours (e.g., 3.75, 2.25)

    Returns:
        str: Time in hh:mm format (e.g., "3:45", "2:15")
    """
    # Extract whole hours
    whole_hours = int(hours)

    # Calculate remaining minutes
    minutes = int((hours - whole_hours) * 60)

    # Format as hh:mm
    return f"{whole_hours}:{minutes:02d}"


def get_ratio(productivity, peripherals):
    pass


def display_ratio():
    pass


def get_sums_for_day(some_datetime):
    program_sum = 0
    domains_sum = 0
    program_entries = program_summary_dao.read_day(some_datetime)
    chrome_entries = chrome_summary_dao.read_day(some_datetime)

    # NOTE: You can MANUALLY change the Chrome flag here.
    # If you count chrome_time in the Program Sum, you are double counting!

    for program in program_entries:
        if program.program_name == "Google Chrome":
            print("SKIPPING google chrome in P Summary")
            continue  # Do not double count
        program_sum += program.hours_spent
    for chrome in chrome_entries:
        domains_sum += chrome.hours_spent

    return program_sum, domains_sum


def get_logs_durations_for_day(some_datetime):
    program_logs_dict = program_logging_dao.read_day_as_sorted(some_datetime)
    domain_logs_dict = chrome_logging_dao.read_day_as_sorted(some_datetime)

    p_log_sum = 0
    ch_log_sum = 0

    # NOTE: You can MANUALLY change the Chrome flag here.
    # If you count chrome_time in the Program Sum, you are double counting!

    for key, value_array in program_logs_dict.items():
        if key == "Google Chrome":
            print("SKIPPING google chrome in P Logs")
        for item in value_array:
            p_log_sum += (item.end_time -
                          item.start_time).seconds / SECONDS_PER_HOUR

    for key, value_array in domain_logs_dict.items():
        for item in value_array:
            ch_log_sum += (item.end_time -
                           item.start_time).seconds / SECONDS_PER_HOUR

    return p_log_sum, ch_log_sum


async def main():
    # week_of_feb_23 = datetime(2025, 2, 23)  # Works in a different development environment
    # week_of_march_2 = datetime(2025, 3, 2)  # Works in a different development environment
    # week_of_march_9 = datetime(2025, 3, 9)  # Works in a different development environment
    # week_of_march_16 = datetime(2025, 3, 16)  # Works in a different development environment

    week_of_april_20 = datetime(2025, 4, 20)
    week_of_april_13 = datetime(2025, 4, 13)

    chosen_week = UserLocalTime(week_of_april_20)

    week_of_productivity = await get_productivity_for_week(chosen_week)

    daily_packages = []

    productivity = {}

    # productivity = get_productive_hours_for_day(
    #     chosen_week, week_of_productivity)

    for i in range(7):
        current_day: UserLocalTime = chosen_week + timedelta(days=i)
        date_as_ult = UserLocalTime(datetime.combine(
            current_day.dt, datetime.min.time()))
        keyboard, mouse = await get_peripherals_for_day(date_as_ult)
        keyboard_sum = sum_hours_for_peripheral(keyboard)
        mouse_sum = sum_hours_for_peripheral(mouse)

        day_of_productivity = get_productivity_for_day(
            date_as_ult, week_of_productivity)

        sums_as_dictated_by_sum_dao = get_sums_for_day(date_as_ult)
        durations_of_log_dao_logs = get_logs_durations_for_day(
            date_as_ult)

        assert day_of_productivity is not None
        package = {
            "day": date_as_ult.dt,
            "keyboard": keyboard,
            "mouse": mouse,
            "total_peripherals": mouse_sum + keyboard_sum,
            "peripherals_hhmm": hours_to_hh_mm(mouse_sum + keyboard_sum),
            "productivity": day_of_productivity["productivity"],
            "leisure": day_of_productivity["leisure"],
            "total_hours": day_of_productivity["productivity"] + day_of_productivity["leisure"],
            "productivity_hhmm": hours_to_hh_mm(day_of_productivity["productivity"] + day_of_productivity["leisure"]),
            "straight_from_sum_dao": sums_as_dictated_by_sum_dao[0] + sums_as_dictated_by_sum_dao[1],
            "straight_from_logs_dao": durations_of_log_dao_logs[0] + durations_of_log_dao_logs[1]
        }
        daily_packages.append(package)

    # Process and display the results
    print("\n\n")
    for package in daily_packages:
        decimal_places = 3
        sums_total = package["straight_from_sum_dao"]
        logs_total = package["straight_from_logs_dao"]
        print(f"Day: {package['day'].strftime('%Y-%m-%d')}")

        print(f"    Day via Sum DAO: {round(sums_total, decimal_places)}")
        print(f"    Day via Logs DAO: {round(logs_total, decimal_places)}")
        if logs_total > 0:
            print(
                f"    Logs over Sums: {round(logs_total / sums_total, decimal_places)}")
        else:
            print(
                f"    Logs total was 0. Sums total was {round(sums_total, decimal_places)}")

        print(f"  Peripherals time: {package['peripherals_hhmm']} ")
        print(
            f"  Programs & Chrome time: {package['productivity_hhmm']} ")

        if package['total_peripherals'] == 0 and package["total_hours"] == 0:
            logger.log_yellow("  *No usage today")
        elif package['total_peripherals'] > 0:
            ratio = package['total_hours'] / package['total_peripherals']
            # print(f"  Ratio (Programs:Peripherals): {ratio:.2f}:1")
            logger.log_green_then_white(
                "  Ratio ", f"(Programs:Peripherals): {ratio:.2f}:1")
            if ratio > 4:
                logger.log_yellow("  WARNING: Unusually high ratio detected!")
        else:
            ratio = str(package["total_hours"]) + ":0"
            print("Total hours: " + str(package["total_hours"]))
            print("BUT total peripherals was somehow 0")

        print()

        # This is how you would run the async function
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


# TODO: Go day by day for the past two weeks.
