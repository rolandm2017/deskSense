from typing import Literal

from pydantic import BaseModel


ActivityState = Literal["active", "idle"]
PursuitCategory = Literal[
    "productivity", "learning", "entertainment", "communication"
]
SourceType = Literal["program", "domain", "video", "video_channel"]


class DailyRange(BaseModel):
    start: str
    end: str


class ActiveIdleTotals(BaseModel):
    activeSeconds: int
    idleSeconds: int
    trackedSeconds: int


class ActiveIdleBlock(BaseModel):
    start: str
    end: str
    state: ActivityState
    durationSeconds: int


class ActiveIdleResponse(BaseModel):
    date: str
    range: DailyRange
    totals: ActiveIdleTotals
    blocks: list[ActiveIdleBlock]


class PursuitAttribution(BaseModel):
    pursuitId: str
    name: str
    category: PursuitCategory | None
    color: str | None


class ActivitySource(BaseModel):
    sourceType: SourceType
    identifier: str
    displayName: str


class ActivityBlock(BaseModel):
    start: str
    end: str
    durationSeconds: int
    label: str


class TopActivityLane(BaseModel):
    rank: int
    sourceType: SourceType
    identifier: str
    displayName: str
    totalSeconds: int
    pursuit: PursuitAttribution
    parentSource: ActivitySource | None
    blocks: list[ActivityBlock]


class TopActivitiesResponse(BaseModel):
    date: str
    range: DailyRange
    limit: int
    mergeGapSeconds: int
    lanes: list[TopActivityLane]
