from datetime import timedelta

from .errors import SuspiciousDurationError
from .console_logger import ConsoleLogger
from .debug_logger import write_to_debug_log, write_to_large_usage_log

logger  = ConsoleLogger()

def notice_suspicious_durations(existing_entry, program_session):
        
    impossibly_long_day = existing_entry.hours_spent > 24
    if impossibly_long_day:
        logger.log_red(
            "[critical] " + str(existing_entry.hours_spent) + " for " + existing_entry.program_name)
        raise SuspiciousDurationError("long day")
    if program_session.duration and program_session.duration > timedelta(hours=1):
        print(program_session, ' ** ** 87ru')
        logger.log_red(
            "[critical] " + str(program_session.duration) + " for " + existing_entry.program_name)
        raise SuspiciousDurationError("duration")
    
def log_if_needed(program_session, target_program_name, usage_duration_in_hours, right_now):
    if program_session.window_title == "Alt-tab window":
        write_to_debug_log(target_program_name, usage_duration_in_hours,
                            right_now.strftime("%m-%d %H:%M:%S"))
    if usage_duration_in_hours > 0.333:
        write_to_large_usage_log(program_session,
                                    usage_duration_in_hours, right_now.strftime("%m-%d %H:%M:%S"))