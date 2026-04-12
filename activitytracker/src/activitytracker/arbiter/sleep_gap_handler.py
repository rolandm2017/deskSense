from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


@dataclass
class SleepGapDecision:
    should_flush: bool
    end_time: UserLocalTime | None


class SleepGapHandler:
    """Decides whether a sleep/wake gap requires flushing the active session.

    Also owns the suspicious-status-write warning, which is a log-only signal
    that the incoming session probably followed a sleep the detector missed.
    """

    _SUSPICIOUS_WRITE_THRESHOLD = timedelta(minutes=2)

    def __init__(self, sleep_detector, logger: ConsoleLogger | None = None):
        self._sleep_detector = sleep_detector
        self._logger = logger or ConsoleLogger()

    def inspect_before_transition(
        self, incoming_session: ProgramSession | ChromeSession
    ) -> SleepGapDecision:
        looks_like_sleep_occurred, time_before_lg_gap = (
            self._sleep_detector.detect_awakening_from_sleep()
        )

        if looks_like_sleep_occurred:
            self._logger.log_yellow_multiple(
                "[warn] detect sleep results:",
                looks_like_sleep_occurred,
                time_before_lg_gap,
            )
            return SleepGapDecision(should_flush=True, end_time=time_before_lg_gap)

        self._maybe_warn_suspicious_write(incoming_session)
        return SleepGapDecision(should_flush=False, end_time=None)

    def _maybe_warn_suspicious_write(
        self, incoming_session: ProgramSession | ChromeSession
    ) -> None:
        latest_status_write = self._sleep_detector.get_latest_write_time()
        if latest_status_write is None:
            return

        incoming_start = incoming_session.start_time
        if (
            latest_status_write.dt
            >= incoming_start.dt - self._SUSPICIOUS_WRITE_THRESHOLD
        ):
            return

        minutes_since_write = (
            incoming_start.dt - latest_status_write.dt
        ).total_seconds() / 60
        self._logger.log_yellow(
            f"[warn] latest status write was {minutes_since_write:.2f} min ago"
        )
