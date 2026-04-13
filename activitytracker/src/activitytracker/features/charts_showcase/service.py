from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from activitytracker.features.charts_showcase.schemas import (
    ActiveIdleBlock,
    ActiveIdleResponse,
    ActiveIdleTotals,
    ActivityBlock,
    ActivitySource,
    DailyRange,
    PursuitAttribution,
    TopActivitiesResponse,
    TopActivityLane,
)


DAY_START_HOUR = 4
MERGE_GAP_SECONDS = 300


@dataclass(frozen=True)
class PresenceBlockSeed:
    start_hour: float
    end_hour: float
    state: str


@dataclass(frozen=True)
class ActivityBlockSeed:
    start_hour: float
    end_hour: float
    label: str


@dataclass(frozen=True)
class ActivityLaneSeed:
    source_type: str
    identifier: str
    display_name: str
    pursuit: PursuitAttribution
    parent_source: ActivitySource | None
    blocks: tuple[ActivityBlockSeed, ...]


PRODUCTIVITY = PursuitAttribution(
    pursuitId="p_productivity_mock",
    name="Productivity Mock",
    category="productivity",
    color="#C7F36B",
)
LEARNING = PursuitAttribution(
    pursuitId="p_learning_mock",
    name="Learning Mock",
    category="learning",
    color="#7DD3C7",
)
COMMUNICATION = PursuitAttribution(
    pursuitId="p_communication_mock",
    name="Communication Mock",
    category="communication",
    color="#E9687A",
)
ENTERTAINMENT = PursuitAttribution(
    pursuitId="p_entertainment_mock",
    name="Entertainment Mock",
    category="entertainment",
    color="#F28A2E",
)
UNCATEGORIZED = PursuitAttribution(
    pursuitId="uncategorized",
    name="Uncategorized",
    category=None,
    color=None,
)

PRESENCE_BLOCKS = (
    PresenceBlockSeed(7.70, 10.50, "active"),
    PresenceBlockSeed(10.50, 10.83, "idle"),
    PresenceBlockSeed(10.83, 12.85, "active"),
    PresenceBlockSeed(12.85, 13.17, "idle"),
    PresenceBlockSeed(13.17, 17.60, "active"),
    PresenceBlockSeed(17.60, 18.00, "idle"),
    PresenceBlockSeed(18.00, 21.33, "active"),
    PresenceBlockSeed(21.33, 21.50, "idle"),
    PresenceBlockSeed(21.50, 23.30, "active"),
)

ACTIVITY_LANES = (
    ActivityLaneSeed(
        "program",
        "Code.exe",
        "VS Code",
        PRODUCTIVITY,
        None,
        (
            ActivityBlockSeed(7.70, 8.10, "DeskSense - main.ts"),
            ActivityBlockSeed(8.33, 10.50, "DeskSense - renderer.ts"),
            ActivityBlockSeed(10.83, 12.20, "DeskSense - chart.ts"),
            ActivityBlockSeed(14.50, 16.83, "Client Project - api.py"),
            ActivityBlockSeed(17.10, 17.60, "Client Project - tests.py"),
            ActivityBlockSeed(21.50, 23.00, "DeskSense - timeline.ts"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "chrome.exe",
        "Chrome",
        PRODUCTIVITY,
        None,
        (
            ActivityBlockSeed(8.10, 8.33, "Stack Overflow - async patterns"),
            ActivityBlockSeed(13.17, 13.50, "MDN Web Docs"),
            ActivityBlockSeed(14.00, 14.50, "Bunpro - Grammar N3"),
            ActivityBlockSeed(19.20, 20.83, "Khan Academy - Linear Algebra"),
            ActivityBlockSeed(23.00, 23.17, "GitHub - pull requests"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "WindowsTerminal.exe",
        "Terminal",
        PRODUCTIVITY,
        None,
        (
            ActivityBlockSeed(7.83, 8.00, "npm run dev"),
            ActivityBlockSeed(8.50, 8.67, "git push"),
            ActivityBlockSeed(10.83, 11.00, "docker compose up"),
            ActivityBlockSeed(14.67, 14.83, "pytest"),
            ActivityBlockSeed(16.83, 17.00, "ssh deploy"),
            ActivityBlockSeed(21.67, 21.83, "npm run build"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "gmail",
        "Gmail",
        COMMUNICATION,
        None,
        (
            ActivityBlockSeed(8.10, 8.30, "Inbox - client correspondence"),
            ActivityBlockSeed(17.00, 17.10, "Inbox - invoicing"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "slack.exe",
        "Slack",
        COMMUNICATION,
        None,
        (
            ActivityBlockSeed(11.00, 11.17, "#dev - standup"),
            ActivityBlockSeed(16.83, 17.10, "#general - EOD updates"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "discord.exe",
        "Discord",
        COMMUNICATION,
        None,
        (ActivityBlockSeed(23.00, 23.30, "Server - dev community"),),
    ),
    ActivityLaneSeed(
        "video_channel",
        "youtube:3blue1brown",
        "YouTube",
        ENTERTAINMENT,
        ActivitySource(
            sourceType="domain",
            identifier="youtube.com",
            displayName="Chrome",
        ),
        (ActivityBlockSeed(12.20, 12.85, "3Blue1Brown - Essence of LA"),),
    ),
    ActivityLaneSeed(
        "program",
        "vlc.exe",
        "VLC Player",
        ENTERTAINMENT,
        None,
        (ActivityBlockSeed(12.50, 12.85, "lecture-recording-04.mkv"),),
    ),
    ActivityLaneSeed(
        "program",
        "anki.exe",
        "Anki",
        LEARNING,
        None,
        (ActivityBlockSeed(13.17, 14.00, "Japanese Core 2000 - Review"),),
    ),
    ActivityLaneSeed(
        "program",
        "factorio.exe",
        "Factorio",
        ENTERTAINMENT,
        None,
        (ActivityBlockSeed(18.00, 19.20, "Nauvis - iron smelting"),),
    ),
    ActivityLaneSeed(
        "program",
        "obsidian.exe",
        "Obsidian",
        PRODUCTIVITY,
        None,
        (
            ActivityBlockSeed(11.17, 11.33, "Daily note - April 7"),
            ActivityBlockSeed(20.83, 21.00, "Math notes - eigenvalues"),
        ),
    ),
    ActivityLaneSeed(
        "program",
        "explorer.exe",
        "File Explorer",
        PRODUCTIVITY,
        None,
        (
            ActivityBlockSeed(11.33, 11.42, "Downloads folder"),
            ActivityBlockSeed(21.00, 21.08, "Projects directory"),
        ),
    ),
)


class ChartsShowcaseService:
    """Temporary hardcoded provider for Activity Overview chart endpoints."""

    def get_active_idle(self, day: date) -> ActiveIdleResponse:
        blocks = [
            ActiveIdleBlock(
                start=_hour_to_iso(day, block.start_hour),
                end=_hour_to_iso(day, block.end_hour),
                state=block.state,
                durationSeconds=_duration_seconds(block.start_hour, block.end_hour),
            )
            for block in PRESENCE_BLOCKS
        ]
        active_seconds = sum(
            block.durationSeconds for block in blocks if block.state == "active"
        )
        idle_seconds = sum(
            block.durationSeconds for block in blocks if block.state == "idle"
        )

        return ActiveIdleResponse(
            date=day.isoformat(),
            range=_daily_range(day),
            totals=ActiveIdleTotals(
                activeSeconds=active_seconds,
                idleSeconds=idle_seconds,
                trackedSeconds=active_seconds + idle_seconds,
            ),
            blocks=blocks,
        )

    def get_top_activities(self, day: date, limit: int) -> TopActivitiesResponse:
        lanes = sorted(
            (
                self._build_activity_lane(day, lane)
                for lane in ACTIVITY_LANES
            ),
            key=lambda lane: (-lane.totalSeconds, lane.displayName),
        )[:limit]

        ranked_lanes = [
            lane.model_copy(update={"rank": rank})
            for rank, lane in enumerate(lanes, start=1)
        ]

        return TopActivitiesResponse(
            date=day.isoformat(),
            range=_daily_range(day),
            limit=limit,
            mergeGapSeconds=MERGE_GAP_SECONDS,
            lanes=ranked_lanes,
        )

    def _build_activity_lane(
        self, day: date, seed: ActivityLaneSeed
    ) -> TopActivityLane:
        blocks = [
            ActivityBlock(
                start=_hour_to_iso(day, block.start_hour),
                end=_hour_to_iso(day, block.end_hour),
                durationSeconds=_duration_seconds(block.start_hour, block.end_hour),
                label=block.label,
            )
            for block in seed.blocks
        ]

        return TopActivityLane(
            rank=0,
            sourceType=seed.source_type,
            identifier=seed.identifier,
            displayName=seed.display_name,
            totalSeconds=sum(block.durationSeconds for block in blocks),
            pursuit=seed.pursuit,
            parentSource=seed.parent_source,
            blocks=blocks,
        )


def get_charts_showcase_service() -> ChartsShowcaseService:
    return ChartsShowcaseService()


def _daily_range(day: date) -> DailyRange:
    start = datetime.combine(day, time(hour=DAY_START_HOUR))
    end = start + timedelta(days=1)
    return DailyRange(start=start.isoformat(), end=end.isoformat())


def _hour_to_iso(day: date, hour: float) -> str:
    whole_hours = int(hour)
    minutes = int(round((hour - whole_hours) * 60))
    base = datetime.combine(day, time())
    return (base + timedelta(hours=whole_hours, minutes=minutes)).isoformat()


def _duration_seconds(start_hour: float, end_hour: float) -> int:
    return int(round((end_hour - start_hour) * 3600))
