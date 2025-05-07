from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from datetime import datetime, timedelta

from typing import List

from activitytracker.db.dao.utility_dao_mixin import UtilityDaoMixin
from activitytracker.db.models import SystemStatus

# from activitytracker.object.enums import SystemStatusType
from activitytracker.object.enums import SystemStatusType
from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_all,
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


class SystemStatusDao(UtilityDaoMixin):
    """
    Exists to use polling to tell when the program is up and running.

    Intent is to create an auditable time to check summaries against.
    """

    def __init__(self, clock: UserFacingClock, sync_session_maker: sessionmaker):
        """Exists mostly for debugging."""
        self.clock = clock  # Must exist via constructor injection
        self.sync_session_maker = sync_session_maker
        self.latest_id = None
        self.logger = ConsoleLogger()

    def run_polling_loop(self):
        on_first_iteration = self.latest_id is None
        current_time = self.clock.now()
        if on_first_iteration:
            self.logger.log_green("info: Writing program startup entry")
            self.add_program_started(current_time)
        else:
            self.logger.log_green("info: continued session")
            self.add_new(current_time)

    def add_program_started(self, current_time) -> None:
        """Used for the first status entry after the program starts up"""
        current_time_utc = convert_to_utc(current_time.dt)
        new_status_log = SystemStatus(
            status=SystemStatusType.PROGRAM_STARTED, created_at=current_time_utc
        )
        id_from_new_write = self.add_new_item(new_status_log)
        # Do not update the latest value. Only do that for the 2nd and later writes.
        # Said another way, updating the latest value would mean
        # updating the final "Shutdown" to "Online"
        self.latest_id = id_from_new_write

    def add_new(self, current_time: UserLocalTime) -> None:
        """
        Writes the current timestamp to the table.
        """
        current_time_utc = convert_to_utc(current_time.dt)
        new_status_log = SystemStatus(
            # It will be updated to "ONLINE" if program continues running
            status=SystemStatusType.SHUTDOWN,
            created_at=current_time_utc,
        )
        id_from_new_write = self.add_new_item(new_status_log)
        # Make the previous newest record a "still online" status
        self.update_latest(self.latest_id)
        self.latest_id = id_from_new_write

    def update_latest(self, latest_id) -> None:
        """Latest_id is stored as a variable for convenience"""
        self.logger.log_green("updating: " + str(latest_id))
        with self.sync_session_maker() as session:
            try:
                # Direct update without fetching first

                stmt = (
                    update(SystemStatus)
                    .where(SystemStatus.id == latest_id)
                    .values(status_type=SystemStatusType.ONLINE)
                )

                session.execute(stmt)
                session.commit()

            except Exception as e:
                session.rollback()
                self.logger.log_yellow(f"Error updating status record: {str(e)}")

    def read_highest_id(self) -> int | None:
        """
        Retrieves the highest ID in the system_change_log table.

        Returns:
            int: The highest ID value, or None if the table is empty
        """
        with self.sync_session_maker() as session:
            try:
                # Use max() function to get the highest ID directly
                from sqlalchemy import func

                result = session.query(func.max(SystemStatus.id)).scalar()
                return result  # Will be None if table is empty

            except Exception as e:
                self.logger.log_yellow(f"Error retrieving highest ID: {str(e)}")
                return None

    def read_day(self, day: UserLocalTime) -> List[SystemStatus]:
        today_start = get_start_of_day_from_datetime(day.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(SystemStatus).where(
            SystemStatus.created_at >= today_start,
            SystemStatus.created_at < tomorrow_start,
        )
        result = self.execute_and_return_all(query)
        return attach_tz_to_all(result, day.dt.tzinfo)  # type: ignore

    def read_all(self) -> List[SystemStatus]:
        """Read all entries."""
        query = select(SystemStatus)
        # Developer handles it manually
        return self.execute_and_return_all(query)
