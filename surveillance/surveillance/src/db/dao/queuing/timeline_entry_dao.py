# timeline_entry_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta, time

from typing import List

from ..base_dao import BaseQueueingDao
from ...models import TimelineEntryObj, PrecomputedTimelineEntry
from ....object.classes import KeyboardAggregate, MouseMoveWindow
from ....object.enums import ChartEventType
from ....util.console_logger import ConsoleLogger
from ....util.timeline_event_aggregator import aggregate_timeline_events


class TimelineEntryDao(BaseQueueingDao):
    def __init__(self, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker, batch_size=batch_size, flush_interval=flush_interval, dao_name="TimelineEntry")

        self.logger = ConsoleLogger()

    async def create_from_keyboard_aggregate(self, content: KeyboardAggregate):
        group = ChartEventType.KEYBOARD
        new_row = TimelineEntryObj(
            group=group,
            start=content.start_time,
            end=content.end_time
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
        # ### aggregate them
        aggregated = aggregate_timeline_events(days_events)

        # ### store them into the db
        rows = []
        for event in aggregated:
            row = PrecomputedTimelineEntry(clientFacingId=event.clientFacingId,
                                           group=event.group,
                                           content=event.content,
                                           start=event.start,
                                           end=event.end,
                                           eventCount=event.eventCount if hasattr(
                                               # Default to 1 if not provided
                                               event, 'eventCount') and event.eventCount is not None else 1
                                           )

            rows.append(row)
        await self.bulk_create_precomputed(rows)

        # return the stored values
        return rows

    async def bulk_create_precomputed(self, rows: List[PrecomputedTimelineEntry]):
        """
        Bulk insert multiple PrecomputedTimelineEntry rows in a single transaction.

        Args:
            rows: List of PrecomputedTimelineEntry instances to insert
        """
        async with self.session_maker() as session:
            async with session.begin():

                session.add_all(rows)
                await session.commit()

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

            # scalars_result = result.scalars()
            # return await await_if_needed(scalars_result)

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
            # scalars_result = result.scalars()
            # return await await_if_needed(scalars_result)

    async def read_day_mice(self, users_systems_day: datetime, user_facing_clock) -> List[TimelineEntryObj]:
        today = user_facing_clock.now().date()
        is_today = today == users_systems_day.date()
        if is_today:
            # Precomputed day can't exist yet
            return await self.read_day(users_systems_day, ChartEventType.MOUSE)
        else:
            # print(users_systems_day, " is not today mouse")
            # return await self.read_day(day, ChartEventType.MOUSE)
            precomputed_day_entries = await self.read_precomputed_entry_for_day(
                users_systems_day, ChartEventType.MOUSE)
            if len(precomputed_day_entries) > 0:
                return precomputed_day_entries
            else:
                read_events = await self.read_day(users_systems_day, ChartEventType.MOUSE)
                new_precomputed_day = await self.create_precomputed_day(read_events)
                return new_precomputed_day

    async def read_day_keyboard(self, users_systems_day: datetime, user_facing_clock) -> List[TimelineEntryObj]:
        today = user_facing_clock.now().date()
        is_today = today == users_systems_day.date()
        if is_today:
            # Precomputed day can't exist yet
            return await self.read_day(users_systems_day, ChartEventType.KEYBOARD)
        else:
            # print(users_systems_day, " is not today keyboard")
            # return await self.read_day(day, ChartEventType.KEYBOARD)
            precomputed_day_entries = await self.read_precomputed_entry_for_day(
                users_systems_day, ChartEventType.KEYBOARD)

            if len(precomputed_day_entries) > 0:
                return precomputed_day_entries
            else:
                read_events = await self.read_day(users_systems_day, ChartEventType.KEYBOARD)
                new_precomputed_day = await self.create_precomputed_day(read_events)

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
