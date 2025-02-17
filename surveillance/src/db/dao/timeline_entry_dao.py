# timeline_entry_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta, time

from typing import List

from .base_dao import BaseQueueingDao
from ..models import TimelineEntryObj, PrecomputedTimelineEntry
from ...object.dto import ProgramDto
from ...object.classes import KeyboardAggregate, MouseMoveWindow
from ...object.enums import ChartEventType
from ...console_logger import ConsoleLogger
from ...util.timeline_event_aggregator import aggregate_timeline_events


class TimelineEntryDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create_from_keyboard_aggregate(self, content: KeyboardAggregate):
        group = ChartEventType.KEYBOARD
        new_row = TimelineEntryObj(
            group=group,
            start=content.session_start_time,
            end=content.session_end_time
        )
        await self.create(new_row)

    async def create_from_mouse_move_window(self, content: MouseMoveWindow):
        group = ChartEventType.MOUSE
        new_row = TimelineEntryObj(
            group=group,
            start=content.start_time,
            end=content.end_time
        )
        await self.create(new_row)

    async def create(self, new_row: TimelineEntryObj):
        await self.queue_item(new_row, TimelineEntryObj)

    async def create_precomputed_day(self, days_events):
        # TODO -- stopping due to finger injury

        # aggregate them
        aggregated = aggregate_timeline_events(days_events)

        # store them into the db
        rows = []
        for event in aggregated:
            row = PrecomputedTimelineEntry(clientFacingId=event.clientFacingId,
                                           group=event.group,
                                           content=event.content,
                                           start=event.start,
                                           end=event.end
                                           )
            rows.append(row)
        # return the stored values
        return rows

    async def read_highest_id(self):
        """Read the highest ID currently in the table"""
        async with self.session_maker() as session:
            query = select(func.max(TimelineEntryObj.id))
            result = await session.execute(query)
            max_id = result.scalar()
            return max_id or 0  # Return 0 if table is empty

    async def read_precomputed_entry_for_day(self, day: datetime, type: ChartEventType):
        # Get start of day (midnight) # time.min is 00:00:00
        start_of_day = datetime.combine(day.date(), time.min)

        # Get end of day (just before midnight) # time.max is 23:59:59.999999
        end_of_day = datetime.combine(day.date(), time.max)
        query = select(PrecomputedTimelineEntry).where(
            PrecomputedTimelineEntry.group == type,
            PrecomputedTimelineEntry.start >= start_of_day,
            PrecomputedTimelineEntry.end <= end_of_day
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_day(self, day: datetime, event_type: ChartEventType) -> List[TimelineEntryObj]:
        """Read all entries for the given day"""
        start_of_day = datetime.combine(day.date(), datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        query = select(TimelineEntryObj).where(
            TimelineEntryObj.start >= start_of_day,
            TimelineEntryObj.start < end_of_day,
            TimelineEntryObj.group == event_type
        ).order_by(TimelineEntryObj.start)

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_day_mice(self, day: datetime) -> List[TimelineEntryObj]:
        is_today = day.strftime(
            "%m %d %Y") == datetime.now().strftime("%m %d %Y")
        if is_today:
            # Precomputed day can't exist yet
            return await self.read_day(day, ChartEventType.MOUSE)
        else:
            # TEMP - so I can ... without computing the day incorrectly
            # return await self.read_day(day, ChartEventType.MOUSE)
            precomputed_day_entries = await self.read_precomputed_entry_for_day(
                day, ChartEventType.MOUSE)
            # FIXME: need to verify that this returns an empty array if the day isnt there yet
            print(precomputed_day_entries, '113ru')
            if len(precomputed_day_entries) > 0:
                return precomputed_day_entries
            else:
                read_events = await self.read_day(day, ChartEventType.MOUSE)
                new_precomputed_day = await self.create_precomputed_day(read_events)
                print(new_precomputed_day, '119ru')
                return new_precomputed_day

    async def read_day_keyboard(self, day: datetime) -> List[TimelineEntryObj]:
        is_today = day.strftime(
            "%m %d %Y") == datetime.now().strftime("%m %d %Y")
        if is_today:
            # Precomputed day can't exist yet
            return await self.read_day(day, ChartEventType.KEYBOARD)
        else:
            # return await self.read_day(day, ChartEventType.KEYBOARD)
            precomputed_day_entries = await self.read_precomputed_entry_for_day(
                day, ChartEventType.KEYBOARD)
            print(precomputed_day_entries, '130ru')
            if len(precomputed_day_entries) > 0:
                return precomputed_day_entries
            else:
                read_events = await self.read_day(day, ChartEventType.KEYBOARD)
                new_precomputed_day = await self.create_precomputed_day(read_events)
                print(new_precomputed_day, '136ru')
                return new_precomputed_day

    async def read_all(self):
        """Read all timeline entries"""
        async with self.session_maker() as session:
            result = await session.execute(select(TimelineEntryObj))
            return result.scalars().all()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(TimelineEntryObj, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
