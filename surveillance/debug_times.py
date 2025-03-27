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

from src.db.database import async_session_maker

from src.object.dashboard_dto import WeeklyProgramContent
from src.object.enums import ChartEventType
from src.services.dashboard_service import DashboardService
from src.db.dao.timeline_entry_dao import TimelineEntryDao
from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.chrome_summary_dao import ChromeSummaryDao

from src.db.dao.program_logs_dao import ProgramLoggingDao
from src.db.dao.chrome_logs_dao import ChromeLoggingDao

from src.db.dao.program_logs_dao import ProgramLoggingDao
from src.db.dao.chrome_logs_dao import ChromeLoggingDao

from src.util.console_logger import ConsoleLogger

logger = ConsoleLogger()


program_logging_dao = ProgramLoggingDao(async_session_maker)
chrome_logging_dao = ChromeLoggingDao(async_session_maker)
program_summary_dao = ProgramSummaryDao(
    program_logging_dao, async_session_maker)
chrome_summary_dao = ChromeSummaryDao(chrome_logging_dao, async_session_maker)
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


async def main():
    week_of_feb_23 = datetime(2025, 2, 23)
    week_of_march_2 = datetime(2025, 3, 2)
    week_of_march_9 = datetime(2025, 3, 9)
    week_of_march_16 = datetime(2025, 3, 16)

    chosen_week = week_of_march_16

    week_of_productivity = await get_productivity_for_week(chosen_week)

    # for v in week_of_productivity:
    #     print(v, '90ru')

    daily_packages = []

    productivity = {}

    # productivity = get_productive_hours_for_day(
    #     chosen_week, week_of_productivity)
    # print(productivity, "100ru")

    for i in range(7):
        current_day = chosen_week + timedelta(days=i)
        date_as_datetime = datetime.combine(
            current_day, datetime.min.time())
        keyboard, mouse = await get_peripherals_for_day(date_as_datetime)
        keyboard_sum = sum_hours_for_peripheral(keyboard)
        mouse_sum = sum_hours_for_peripheral(mouse)

        day_of_productivity = get_productivity_for_day(
            date_as_datetime, week_of_productivity)

        assert day_of_productivity is not None
        package = {
            "day": date_as_datetime,
            "keyboard": keyboard,
            "mouse": mouse,
            "total_peripherals": mouse_sum + keyboard_sum,
            "peripherals_hhmm": hours_to_hh_mm(mouse_sum + keyboard_sum),
            "productivity": day_of_productivity["productivity"],
            "leisure": day_of_productivity["leisure"],
            "total_hours": day_of_productivity["productivity"] + day_of_productivity["leisure"],
            "productivity_hhmm": hours_to_hh_mm(day_of_productivity["productivity"] + day_of_productivity["leisure"])
        }
        daily_packages.append(package)

    # Process and display the results
    for package in daily_packages:
        print(f"Day: {package['day'].strftime('%Y-%m-%d')}")
        print(f"  Peripherals time: {package['peripherals_hhmm']} ")
        print(
            f"  Programs & Chrome time: {package['productivity_hhmm']} ")
        if package['total_peripherals'] == 0 and package["total_hours"] == 0:
            print("  *No usage today")
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

# week_of_march_2 = datetime(2025, 3, 2)
# week_of_feb_23 = datetime(2025, 2, 23)


# week_of_productivity = get_productivity_for_week(week_of_march_2)

# daily_packages = []

# for i in range(7):
#     current_day = week_of_march_2 + timedelta(days=i)
#     date_as_datetime = datetime.combine(
#         current_day, datetime.min.time())
#     keyboard, mouse = await get_peripherals_for_day(date_as_datetime)
#     keyboard_sum = sum_hours_for_peripheral(keyboard)
#     mouse_sum = sum_hours_for_peripheral(mouse)
#     productivity = get_productive_hours_for_day(
#         date_as_datetime, week_of_productivity)
#     assert productivity is not None
#     package = {
#         "day": date_as_datetime,
#         "keyboard": keyboard,
#         "mouse": mouse,
#         "total_peripherals": mouse_sum + keyboard_sum,
#         "productivity": productivity["productivity"],
#         "leisure":  productivity["leisure"],
#         "total_hours": productivity["productivity"] + productivity["leisure"]

#     }
