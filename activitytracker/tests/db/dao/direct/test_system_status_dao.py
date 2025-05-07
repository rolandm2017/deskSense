import psutil
import pytest_asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

import pytz
from datetime import date, datetime, timedelta, timezone

from typing import cast

from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.db.models import Base, SystemStatus
from activitytracker.object.enums import SystemStatusType
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.time_wrappers import UserLocalTime

from ....mocks.mock_clock import MockClock, UserLocalTimeMockClock

tokyo_tz_str = "Asia/Tokyo"
tokyo_tz = pytz.timezone(tokyo_tz_str)


def test_add_program_started(db_session_in_mem):
    """Create a DAO instance with the session maker"""

    dt1 = tokyo_tz.localize(datetime.now() - timedelta(seconds=20))
    dt2 = UserLocalTime(dt1 + timedelta(seconds=1))
    dt3 = UserLocalTime(dt1 + timedelta(seconds=2))
    times = [dt2, dt3]
    clock = UserLocalTimeMockClock(times)

    dao = SystemStatusDao(cast(UserFacingClock, clock), db_session_in_mem)

    add_new_item_spy = Mock(side_effect=dao.add_new_item)
    dao.add_new_item = add_new_item_spy

    make_status_log_spy = Mock(side_effect=dao.make_status_log)
    dao.make_status_log = make_status_log_spy

    # Test setup conditions
    assert dao.latest_id is None

    some_ult = dao.clock.now()

    dao.add_activitytracker_started(some_ult)

    assert dao.latest_id is not None
    assert isinstance(dao.latest_id, int)

    add_new_item_spy.assert_called_once()

    status_obj = add_new_item_spy.call_args_list[0][0][0]
    assert isinstance(status_obj, SystemStatus)


def test_add_new_log(db_session_in_mem):
    """Create a DAO instance with the session maker"""

    dt1 = tokyo_tz.localize(datetime.now() - timedelta(seconds=20))
    dt2 = UserLocalTime(dt1 + timedelta(seconds=1))
    dt3 = UserLocalTime(dt1 + timedelta(seconds=2))
    times = [dt2, dt3]
    clock = UserLocalTimeMockClock(times)

    dao = SystemStatusDao(cast(UserFacingClock, clock), db_session_in_mem)

    test_id = 43

    add_new_item_spy = Mock(return_value=test_id)
    dao.add_new_item = add_new_item_spy

    make_status_log_spy = Mock(side_effect=dao.make_status_log)
    dao.make_status_log = make_status_log_spy

    mark_prior_entry_online_spy = Mock(side_effect=dao.mark_prior_entry_online)
    dao.mark_prior_entry_online = mark_prior_entry_online_spy

    # Test setup conditions
    assert dao.latest_id is None

    some_ult = dao.clock.now()

    # Note: This test is testing a call that happens after the first polling loop
    # so the latest_id actually exists!
    already_existing_id = test_id - 1
    dao.latest_id = already_existing_id

    # -- Act
    dao.add_new_log(some_ult)

    # -- Assert
    assert dao.latest_id is not None
    assert isinstance(dao.latest_id, int)

    add_new_item_spy.assert_called_once()

    status_obj = add_new_item_spy.call_args_list[0][0][0]
    assert isinstance(status_obj, SystemStatus)

    mark_prior_entry_online_spy.assert_called_once()

    id_arg = mark_prior_entry_online_spy.call_args_list[0][0][0]

    assert isinstance(id_arg, int)
    assert dao.latest_id == test_id
    assert id_arg == already_existing_id


def test_run_polling_loop(db_session_in_mem):
    dt1 = tokyo_tz.localize(datetime.now() - timedelta(seconds=20))
    dt2 = UserLocalTime(dt1 + timedelta(seconds=1))
    dt3 = UserLocalTime(dt1 + timedelta(seconds=2))
    dt4 = UserLocalTime(dt1 + timedelta(seconds=3))
    dt5 = UserLocalTime(dt1 + timedelta(seconds=4))
    times = [dt2, dt3, dt4, dt5]
    clock = UserLocalTimeMockClock(times)

    dao = SystemStatusDao(cast(UserFacingClock, clock), db_session_in_mem)

    add_activitytracker_started_spy = Mock(side_effect=dao.add_activitytracker_started)
    dao.add_activitytracker_started = add_activitytracker_started_spy

    add_new_log_spy = Mock(side_effect=dao.add_new_log)
    dao.add_new_log = add_new_log_spy

    add_new_item_spy = Mock(side_effect=dao.add_new_item)
    dao.add_new_item = add_new_item_spy

    make_status_log_spy = Mock(side_effect=dao.make_status_log)
    dao.make_status_log = make_status_log_spy

    mark_prior_entry_online_spy = Mock(side_effect=dao.mark_prior_entry_online)
    dao.mark_prior_entry_online = mark_prior_entry_online_spy

    # -- Act
    dao.run_polling_loop()

    # -- Assert
    saved_id = dao.latest_id
    assert isinstance(dao.latest_id, int)
    add_activitytracker_started_spy.assert_called_once()

    make_status_log_spy.assert_called_once()

    status_type = make_status_log_spy.call_args_list[0][0][0]

    assert status_type == SystemStatusType.PROGRAM_STARTED

    add_activitytracker_started_spy.reset_mock()

    # -- Act - Run the loop again
    dao.run_polling_loop()
    # add_new_item_spy.assertcalledonce

    # -- Assert
    saved_id_2 = dao.latest_id
    assert saved_id != saved_id_2
    assert isinstance(dao.latest_id, int)

    add_activitytracker_started_spy.assert_not_called()

    add_new_log_spy.assert_called_once()

    # -- Act
    dao.run_polling_loop()
    # -- Assert
    assert add_new_log_spy.call_count == 2
