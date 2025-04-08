
from typing import List, TypedDict

from datetime import datetime

from surveillance.src.db.models import DailyDomainSummary


class DaySummary(TypedDict):
    day: datetime
    summaries: List[DailyDomainSummary]
