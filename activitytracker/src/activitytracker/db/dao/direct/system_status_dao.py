from collections import deque

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
    attach_tz_to_created_at_field_for_status,
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

    def __init__(
        self,
        clock: UserFacingClock,
        polling_interval: int | float,
        sync_session_maker: sessionmaker,
    ):
        """Exists mostly for debugging."""
        self.clock = clock  # Must exist via constructor injection
        self.regular_session = sync_session_maker
        self.polling_interval_in_sec = (
            polling_interval  # Must be the same as Periodic Task's
        )
        self.logs_queue = deque(maxlen=10)
        self.latest_id = None
        self.latest_write_time = None
        self.logger = ConsoleLogger()

    def run_polling_loop(self):
        on_first_iteration = self.latest_id is None
        current_time = self.clock.now()
        self.push_pulse_time_to_history(current_time)
        self.latest_write_time = current_time
        if on_first_iteration:
            self.logger.log_green("info: Writing program startup entry\n")
            self.add_activitytracker_started(current_time)
        else:
            self.add_new_log(current_time)

    def get_latest_write_time(self):
        return self.latest_write_time

    def add_activitytracker_started(self, current_time) -> None:
        """Used for the first status entry after the program starts up"""
        current_time_utc = convert_to_utc(current_time.dt)
        new_status_log = self.make_status_log(
            SystemStatusType.PROGRAM_STARTED, current_time_utc
        )
        id_from_new_write = self.add_new_item(new_status_log)
        # Do not update the latest value. Only do that for the 2nd and later writes.
        # Said another way, updating the latest value would mean
        # updating the final "Shutdown" to "Online"
        self.latest_id = id_from_new_write

    def add_new_log(self, current_time: UserLocalTime) -> None:
        """
        Writes the current timestamp to the table.
        """
        current_time_utc = convert_to_utc(current_time.dt)
        # It will be updated to "ONLINE" if program continues running
        new_status_log = self.make_status_log(SystemStatusType.SHUTDOWN, current_time_utc)
        self.latest_status = new_status_log
        id_from_new_write = self.add_new_item(new_status_log)
        # Make the previous newest record a "still online" status
        self.mark_prior_entry_online(self.latest_id)
        self.latest_id = id_from_new_write

    def make_status_log(self, type_of_status: SystemStatusType, utc_datetime):
        return SystemStatus(
            status=type_of_status.value,  # Must use .value or Pg complains
            created_at=utc_datetime,
        )

    def mark_prior_entry_online(self, latest_id) -> None:
        """Latest_id is stored as a variable for convenience"""
        # self.logger.log_green("updating: " + str(latest_id))
        with self.regular_session() as session:
            try:
                # Direct update without fetching first

                stmt = (
                    update(SystemStatus)
                    .where(SystemStatus.id == latest_id)
                    .values(status=SystemStatusType.ONLINE.value)
                )

                session.execute(stmt)
                session.commit()

            except Exception as e:
                session.rollback()
                self.logger.log_yellow(f"Error updating status record: {str(e)}")

    def detect_awakening_from_sleep(self):
        return self.a_large_gap_exists_between_pulses()

    def a_large_gap_exists_between_pulses(self):
        """
        Intends to detect times when the computer was asleep.

        Problem statement: A session is open and the user sleeps the machine
        for 6 hours. On awakening, the program will then perceive a session
        that lasted for 6 whole hours. In fact the session was like a minute
        long, but the program can't perceive sleep events.

        Solution statement: Record pulse times. Assume a large gap
        is the computer being asleep, program stored in memory.
        """
        # 30 sec gap from 10, highly unusual
        acceptable_duration = self.polling_interval_in_sec * 3

        measured_gaps = self._measure_gaps_between_pulses()
        for gap in measured_gaps:
            if gap["duration"] > acceptable_duration:
                self._avoid_detecting_same_gap_twice()
                return True, gap["start_of_gap"]
        return False, None

    def _avoid_detecting_same_gap_twice(self):
        """Resets the queue so the same gap can't be detected twice"""
        self.logs_queue = deque(maxlen=self.logs_queue.maxlen)

    def _measure_gaps_between_pulses(self):
        gaps = []
        prev = None
        for i, item in enumerate(self.logs_queue):
            if i == 0:
                prev = item
                continue
            current = item
            duration = current - prev
            duration = duration.total_seconds()
            gaps.append({"duration": duration, "start_of_gap": prev})

            prev = current

        return gaps

    def push_pulse_time_to_history(self, time):
        self.logs_queue.append(time)

    def read_highest_id(self) -> int | None:
        """
        Retrieves the highest ID in the system_status table.

        Returns:
            int: The highest ID value, or None if the table is empty
        """
        with self.regular_session() as session:
            try:
                # Use max() function to get the highest ID directly
                from sqlalchemy import func

                result = session.query(func.max(SystemStatus.id)).scalar()
                return result  # Will be None if table is empty

            except Exception as e:
                self.logger.log_yellow(f"Error retrieving highest ID: {str(e)}")
                return None

    def read_latest(self) -> SystemStatus | None:
        """
        Retrieves the latest SystemStatus record (with highest ID).

        Returns:
            SystemStatus: The most recent status record, or None if table is empty
        """
        with self.regular_session() as session:
            try:
                # Direct query for the latest record by ID descending
                latest_record = (
                    session.query(SystemStatus).order_by(SystemStatus.id.desc()).first()
                )

                if latest_record and latest_record.created_at:
                    # Convert timezone if record exists and has timestamp
                    return attach_tz_to_created_at_field_for_status(
                        latest_record, self.clock.now().dt.tzinfo
                    )
                return latest_record

            except Exception as e:
                self.logger.log_yellow(f"Error retrieving latest status record: {str(e)}")
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
