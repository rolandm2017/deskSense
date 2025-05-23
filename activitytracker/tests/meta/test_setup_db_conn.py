import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock


from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy import text

from activitytracker.db.models import Base
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao

"""
File exists to end the problem with "cannot await coroutine!"
and other such nonsense irritations when trying to
set up and run a DB connection during a DAO test.

Offenders: 
1. TypeError: 'coroutine' object is not callable
"""

# You can cause OSError by putting "gc.collect" after the engine dispose in conftest.py
# and then running the below test, even with read_all() commented out.


@pytest.mark.asyncio
async def test_plain_async_engine(regular_session_maker, async_engine_and_asm):

    # Try to use it
    log_dao = ProgramLoggingDao(regular_session_maker)
    sum_dao = ProgramSummaryDao(log_dao, regular_session_maker)

    all_summaries = sum_dao.read_all()
    all_logs = log_dao.read_all()

    assert 1 == 1
    assert all_summaries is not None
    assert all_logs is not None

    assert isinstance(all_summaries, list)
    assert isinstance(all_logs, list)


def test_sqlite(db_session_in_mem, async_db_session_in_mem):
    # Try to use it
    session_maker = db_session_in_mem
    log_dao = ProgramLoggingDao(session_maker)
    sum_dao = ProgramSummaryDao(log_dao, session_maker)

    all_summaries = sum_dao.read_all()
    all_logs = log_dao.read_all()

    assert all_summaries is not None
    assert all_logs is not None

    for v in all_logs:
        print(v)
    for v in all_summaries:
        print(v)
    assert len(all_summaries) == 0
    assert len(all_logs) == 0
