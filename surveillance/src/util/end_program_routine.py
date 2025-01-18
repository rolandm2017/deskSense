from ..console_logger import ConsoleLogger

logger = ConsoleLogger()

def end_program_readout(report):
    # prints the generated report
    logger.log_red(report)

def pretend_report_event(report):
    logger.log_blue(report)