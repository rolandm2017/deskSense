
from typing import List, TypedDict

from datetime import datetime

from ..db.models import DailyDomainSummary


# TODO: move into utility file if more of these show up
class DaySummary(TypedDict):
    day: datetime
    summaries: List[DailyDomainSummary]
