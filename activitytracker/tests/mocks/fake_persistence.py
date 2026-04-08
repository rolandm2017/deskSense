from __future__ import annotations

from datetime import timedelta
from typing import Generic, TypeVar

from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    DailyVideoSummary,
    DomainActivityLog,
    MysteryMedia,
    ProgramActivityLog,
    SystemStatus,
    VideoActivityLog,
)
from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    CompletedVideoSession,
    ProgramSession,
    VideoSession,
)
from activitytracker.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.const import SECONDS_PER_HOUR

SummaryT = TypeVar(
    "SummaryT", DailyProgramSummary, DailyDomainSummary, DailyVideoSummary
)
LogT = TypeVar("LogT", ProgramActivityLog, DomainActivityLog, VideoActivityLog)


class FakeSystemStatusDao:
    def __init__(self):
        self.polling_interval_in_sec = 10
        self.latest_write_time = None
        self.statuses: list[SystemStatus] = []

    def detect_awakening_from_sleep(self):
        return False, None

    def get_latest_write_time(self):
        return self.latest_write_time

    def read_latest(self):
        return self.statuses[-1] if self.statuses else None

    def run_polling_loop(self):
        return None


class _BaseFakeDao:
    def __init__(self):
        self._id = 1

    def _assign_id(self, model):
        if getattr(model, "id", None) is None:
            model.id = self._id
            self._id += 1
        return model


class _BaseFakeLoggingDao(_BaseFakeDao, Generic[LogT]):
    def __init__(self):
        super().__init__()
        self.logs: list[LogT] = []

    def add_new_item(self, item: LogT):
        self.logs.append(self._assign_id(item))
        return item.id

    def update_item(self, item: LogT):
        return item

    def execute_and_read_one_or_none(self, _query):
        return None

    def read_all(self):
        return list(self.logs)


class _BaseFakeSummaryDao(_BaseFakeDao, Generic[SummaryT]):
    def __init__(self):
        super().__init__()
        self.summaries: list[SummaryT] = []

    def add_new_item(self, item: SummaryT):
        self.summaries.append(self._assign_id(item))
        return item.id

    def read_all(self):
        return list(self.summaries)


class FakeProgramLoggingDao(_BaseFakeLoggingDao[ProgramActivityLog]):
    def start_session(self, session: ProgramSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        start_of_day = convert_to_utc(get_start_of_day_from_datetime(session.start_time.dt))
        end_utc = start_utc + timedelta(seconds=10)
        log = ProgramActivityLog(
            exe_path_as_id=session.exe_path,
            process_name=session.process_name,
            program_name=session.window_title,
            hours_spent=0,
            start_time=start_utc,
            start_time_local=session.start_time.dt,
            end_time=end_utc,
            end_time_local=end_utc.replace(tzinfo=None),
            duration_in_sec=0,
            gathering_date=start_of_day,
            gathering_date_local=start_of_day.replace(tzinfo=None),
            created_at=start_utc,
        )
        self.add_new_item(log)

    def find_session(self, session: ProgramSession | CompletedProgramSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        for log in self.logs:
            if log.start_time == start_utc:
                return log
        return None

    def push_window_ahead_ten_sec(self, session: ProgramSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Program log missing for window push")
        log.duration_in_sec += 10
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedProgramSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Program log missing for finalize")
        duration = (session.end_time.dt - session.start_time.dt).total_seconds()
        log.duration_in_sec = duration
        log.end_time = convert_to_utc(session.end_time.get_dt_for_db())
        log.end_time_local = session.end_time.dt
        self.update_item(log)


class FakeChromeLoggingDao(_BaseFakeLoggingDao[DomainActivityLog]):
    def start_session(self, session: ChromeSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        start_of_day = convert_to_utc(get_start_of_day_from_datetime(session.start_time.dt))
        end_utc = start_utc + timedelta(seconds=10)
        log = DomainActivityLog(
            domain_name=session.domain,
            hours_spent=0,
            start_time=start_utc,
            start_time_local=session.start_time.dt,
            end_time=end_utc,
            end_time_local=end_utc.replace(tzinfo=None),
            duration_in_sec=0,
            gathering_date=start_of_day,
            gathering_date_local=start_of_day.replace(tzinfo=None),
            created_at=start_utc,
        )
        self.add_new_item(log)

    def find_session(self, session: ChromeSession | CompletedChromeSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        for log in self.logs:
            if log.start_time == start_utc:
                return log
        return None

    def push_window_ahead_ten_sec(self, session: ChromeSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Chrome log missing for window push")
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedChromeSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Chrome log missing for finalize")
        duration = (session.end_time.dt - session.start_time.dt).total_seconds()
        log.duration_in_sec = duration
        log.end_time = convert_to_utc(session.end_time.get_dt_for_db())
        log.end_time_local = session.end_time.dt
        self.update_item(log)


class FakeVideoLoggingDao(_BaseFakeLoggingDao[VideoActivityLog]):
    def start_session(self, session: VideoSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        start_of_day = convert_to_utc(get_start_of_day_from_datetime(session.start_time.dt))
        end_utc = start_utc + timedelta(seconds=10)
        log = VideoActivityLog(
            video_id=session.video_info.video_id,
            media_name=session.media_title,
            platform=session.video_info.get_platform_title(),
            hours_spent=0,
            start_time=start_utc,
            start_time_local=session.start_time.dt,
            end_time=end_utc,
            end_time_local=end_utc.replace(tzinfo=None),
            duration_in_sec=0,
            gathering_date=start_of_day,
            gathering_date_local=start_of_day.replace(tzinfo=None),
            created_at=start_utc,
        )
        self.add_new_item(log)

    def find_session(self, session: VideoSession | CompletedVideoSession):
        start_utc = convert_to_utc(session.start_time.get_dt_for_db())
        for log in self.logs:
            if log.start_time == start_utc:
                return log
        return None

    def push_window_ahead_ten_sec(self, session: VideoSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Video log missing for window push")
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedVideoSession):
        log = self.find_session(session)
        if log is None:
            raise ValueError("Video log missing for finalize")
        duration = (session.end_time.dt - session.start_time.dt).total_seconds()
        log.duration_in_sec = duration
        log.end_time = convert_to_utc(session.end_time.get_dt_for_db())
        log.end_time_local = session.end_time.dt
        self.update_item(log)

    def update_name_for_mystery(self, previously_mysterious_id: str, discovered_media_title: str):
        for log in self.logs:
            if (
                log.video_id == previously_mysterious_id
                and log.media_name == "Unknown Watch Page"
            ):
                log.media_name = discovered_media_title


class FakeProgramSummaryDao(_BaseFakeSummaryDao[DailyProgramSummary]):
    def start_session(self, session: ProgramSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        summary = DailyProgramSummary(
            exe_path_as_id=session.exe_path,
            process_name=session.process_name,
            program_name=session.window_title,
            hours_spent=0,
            gathering_date=day_start,
            gathering_date_local=day_start.replace(tzinfo=None),
        )
        self.add_new_item(summary)

    def find_todays_entry_for_program(self, session: ProgramSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        for summary in self.summaries:
            if (
                summary.exe_path_as_id == session.exe_path
                and summary.gathering_date == day_start
            ):
                return summary
        return None

    def push_window_ahead_ten_sec(self, session: ProgramSession):
        summary = self.find_todays_entry_for_program(session)
        if summary is None:
            raise ValueError("Program summary missing for window push")
        summary.hours_spent += 10 / SECONDS_PER_HOUR

    def add_used_time(self, session: ProgramSession, duration_in_sec: int):
        if duration_in_sec == 0:
            return
        summary = self.find_todays_entry_for_program(session)
        if summary is None:
            raise ValueError("Program summary missing for partial add")
        summary.hours_spent += duration_in_sec / SECONDS_PER_HOUR


class FakeChromeSummaryDao(_BaseFakeSummaryDao[DailyDomainSummary]):
    def start_session(self, session: ChromeSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        summary = DailyDomainSummary(
            domain_name=session.domain,
            hours_spent=0,
            gathering_date=day_start,
            gathering_date_local=day_start.replace(tzinfo=None),
        )
        self.add_new_item(summary)

    def find_todays_entry_for_domain(self, session: ChromeSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        for summary in self.summaries:
            if (
                summary.domain_name == session.domain
                and summary.gathering_date == day_start
            ):
                return summary
        return None

    def push_window_ahead_ten_sec(self, session: ChromeSession):
        summary = self.find_todays_entry_for_domain(session)
        if summary is None:
            raise ValueError("Chrome summary missing for window push")
        summary.hours_spent += 10 / SECONDS_PER_HOUR

    def add_used_time(self, session: ChromeSession, duration_in_sec: int):
        if duration_in_sec == 0:
            return
        summary = self.find_todays_entry_for_domain(session)
        if summary is None:
            raise ValueError("Chrome summary missing for partial add")
        summary.hours_spent += duration_in_sec / SECONDS_PER_HOUR


class FakeVideoSummaryDao(_BaseFakeSummaryDao[DailyVideoSummary]):
    def start_session(self, session: VideoSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        summary = DailyVideoSummary(
            video_id=session.video_info.video_id,
            media_name=session.media_title,
            channel_name=None,
            platform=session.video_info.get_platform_title(),
            hours_spent=0,
            gathering_date=day_start,
            gathering_date_local=day_start.replace(tzinfo=None),
        )
        self.add_new_item(summary)

    def find_todays_entry_for_media(self, session: VideoSession):
        day_start = get_start_of_day_from_datetime(session.start_time.dt)
        for summary in self.summaries:
            if (
                summary.media_name == session.media_title
                and summary.gathering_date == day_start
            ):
                return summary
        return None

    def find_netflix_media_by_id(self, media_id: str):
        for summary in reversed(self.summaries):
            if summary.video_id == media_id and summary.platform == "Netflix":
                return summary
        return None

    def update_name_for_mystery(self, previously_mysterious_id: str, discovered_media_title: str):
        for summary in self.summaries:
            if (
                summary.video_id == previously_mysterious_id
                and summary.media_name == "Unknown Watch Page"
            ):
                summary.media_name = discovered_media_title

    def push_window_ahead_ten_sec(self, session: VideoSession):
        summary = self.find_todays_entry_for_media(session)
        if summary is None:
            raise ValueError("Video summary missing for window push")
        summary.hours_spent += 10 / SECONDS_PER_HOUR

    def add_used_time(self, session: VideoSession, duration_in_sec: int):
        if duration_in_sec == 0:
            return
        summary = self.find_todays_entry_for_media(session)
        if summary is None:
            raise ValueError("Video summary missing for partial add")
        summary.hours_spent += duration_in_sec / SECONDS_PER_HOUR


class FakeMysteryMediaDao(_BaseFakeDao):
    def __init__(self):
        super().__init__()
        self.rows: list[MysteryMedia] = []

    def add_new_item(self, item: MysteryMedia):
        self.rows.append(self._assign_id(item))
        return item.id

    def find_most_recent_fifty(self):
        return list(self.rows[-50:])

    def find_by_id(self, mystery_id: str):
        for row in reversed(self.rows):
            if row.mystery_id == mystery_id:
                return row
        return None

    def create(self, mystery_id, discovery_time):
        item = MysteryMedia(
            mystery_id=mystery_id,
            last_seen=convert_to_utc(discovery_time.dt),
        )
        self.add_new_item(item)

    def delete_by_mystery_id(self, mystery_id: str):
        original = len(self.rows)
        self.rows = [row for row in self.rows if row.mystery_id != mystery_id]
        return original - len(self.rows)
