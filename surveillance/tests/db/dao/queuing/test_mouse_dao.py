import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock, patch
import asyncio

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text

from typing import cast

from surveillance.src.db.dao.queuing.mouse_dao import MouseDao
from surveillance.src.db.models import MouseMove
from surveillance.src.object.classes import MouseMoveWindow
from surveillance.src.util.clock import SystemClock

async def truncate_test_tables(async_engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.
    async with async_engine.begin() as conn:
        await conn.execute(text("TRUNCATE mouse_moves RESTART IDENTITY CASCADE"))
        print("Tables truncated")
class TestMouseDao:
    @pytest_asyncio.fixture
    async def dao(self, async_engine_and_asm):
        engine, asm = async_engine_and_asm
        print("Here, 40ruy")
        dao = MouseDao(asm)
        yield dao
        await dao.cleanup()
        
        await truncate_test_tables(engine)
        # await truncate_table(asm)


    @pytest.mark.asyncio
    @pytest.mark.timeout(3)
    async def test_create_from_start_end_times(self, dao):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)

        original_queue_item = dao.queue_item
        queue_item_spy = AsyncMock(side_effect=original_queue_item)
        dao.queue_item = queue_item_spy


        await dao.create_from_start_end_times(start_time, end_time)


        queue_item_spy.assert_called_once()

        queued_item = queue_item_spy.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert cast(datetime, queued_item.start_time) == start_time
        assert cast(datetime, queued_item.end_time) == end_time

    @pytest.mark.asyncio
    @pytest.mark.timeout(3)
    async def test_create_from_window(self, dao):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)
        window = MouseMoveWindow(start_time, end_time)

        original_queue_item = dao.queue_item
        queue_item_spy = AsyncMock(side_effect=original_queue_item)
        dao.queue_item = queue_item_spy

        await dao.create_from_window(window)

        queue_item_spy.assert_called_once()

        queued_item = queue_item_spy.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert cast(datetime, queued_item.start_time) == start_time
        assert cast(datetime, queued_item.end_time) == end_time

    @pytest.mark.asyncio
    @pytest.mark.timeout(3)
    async def test_read_by_id(self, dao):
                
        # Test abandoned because, (a) seems there's never a need to read by ID
        # and (b) seems the create methods don't ever return values, hence, can't know the ID

        # Test reading specific move
        t0 = datetime.now()
        t1 = t0 - timedelta(seconds=25)
        t2 = t0 - timedelta(seconds=23)
        t3 = t0 - timedelta(seconds=21)
        test_window: MouseMoveWindow = MouseMoveWindow(start_of_window=t1, end_of_window=t2)
        test_win_2: MouseMoveWindow = MouseMoveWindow(start_of_window=t2, end_of_window=t3)

        # Arrange
        await dao.create_from_window(test_window)
        await dao.create_from_window(test_win_2)
        await dao._force_process_queue()

        all = await dao.read_all()
        # test setup conditions
        assert len(all) >= 2, "Something wasn't written as expected"
        # Act
        test_subject = all[0]
        
        subject = await dao.read_by_id(test_subject.id)
        # Assert
        assert subject is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(3)
    async def test_read_all(self, dao):
        # Test reading all moves
        t0 = datetime.now(timezone.utc)
        t1 = t0 - timedelta(seconds=10)
        t2 = t0 - timedelta(seconds=8)
        t3 = t0 - timedelta(seconds=6)
        test_1: MouseMoveWindow = MouseMoveWindow(start_of_window=t1, end_of_window=t2)
        test_2: MouseMoveWindow = MouseMoveWindow(start_of_window=t2, end_of_window=t3)

        # Arrange
        await dao.create_from_window(test_1)
        await dao.create_from_window(test_2)
        await dao._force_process_queue()

        
        # Act
        result = await dao.read_all()

        # Assert
        assert len(result) == len([test_1, test_2])
        times = [result[0].start_time, result[1].start_time]
        assert t1 in times, "Window didn't come out of the db as expected"
        assert t2 in times, "Window didn't come out of the db as expected"

    @pytest.mark.asyncio
    @pytest.mark.timeout(3)
    async def test_read_past_24h_events(self, dao):
        t0 = datetime.now(timezone.utc)

        # Today:
        t1 = t0 - timedelta(seconds=10)
        t2 = t0 - timedelta(seconds=8)
        t3 = t0 - timedelta(seconds=6)
        test_1: MouseMoveWindow = MouseMoveWindow(start_of_window=t1, end_of_window=t2)
        test_2: MouseMoveWindow = MouseMoveWindow(start_of_window=t2, end_of_window=t3)

        # A long time ago:
        t5 = t0 - timedelta(days=4, hours=12, seconds=44)
        t6 = t0 - timedelta(days=4, hours=12, seconds=42)
        t7 = t0 - timedelta(days=4, hours=12, seconds=40)
        ancient_test = MouseMoveWindow(start_of_window=t5, end_of_window=t6)
        ancient_test_2 = MouseMoveWindow(start_of_window=t6, end_of_window=t7)

        todays_events = [test_1, test_2]

        # ### Arrange
        # assert 1 == 2
        for e in [test_1, test_2, ancient_test, ancient_test_2]:
            await dao.create_from_window(e)
        await dao._force_process_queue()

        # assert 1 == 1
        # # ### Act
        past_day = await dao.read_past_24h_events(t0)

        # # Assert
        all_events = await dao.read_all()
        assert len(past_day) == len(todays_events)
        assert len(past_day) != len(all_events)
    

    @pytest.mark.asyncio
    async def test_delete(self, dao):
        # mock_move = MouseMove(
        #     id=1, start_time=datetime.now(), end_time=datetime.now())
        # mock_session.get.return_value = mock_move

        t0 = datetime.now(timezone.utc)

        # Today:
        t1 = t0 - timedelta(seconds=10)
        t2 = t0 - timedelta(seconds=8)
        test_window: MouseMoveWindow = MouseMoveWindow(start_of_window=t1, end_of_window=t2)
        
        # Arrange
        await dao.create_from_window(test_window)
        await dao._force_process_queue()

        # Act
        result = await dao.delete(1)

        # Assert
        assert result.start_time == test_window.start_time
        assert result.id == 1  # The ID it had before being deleted
        all_events = await dao.read_all()
        assert test_window not in all_events, "Failed to delete id=1"

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, dao):
        
        # Some ID that almost certainly isn't there
        some_id = 9000

        result = await dao.delete(some_id)

        assert result is None

