from surveillance.src.util.time_formatting import convert_to_utc
from surveillance.src.util.errors import ImpossibleToGetHereError

# pyright: reportAttributeAccessIssue=false

class LoggingDaoMixin:
    def attach_final_values_and_update(self, session, log):
        finalized_duration = (session.end_time.dt - session.start_time.dt).total_seconds()        
        if finalized_duration < 0:
            raise ImpossibleToGetHereError("A negative duration is impossible")
        discovered_final_val = convert_to_utc(session.end_time.get_dt_for_db()).replace(tzinfo=None)

        # Replace whatever used to be there
        log.duration_in_sec = finalized_duration
        log.end_time = discovered_final_val
        log.end_time_local = session.end_time.dt
        self.update_item(log)