import pytest
import pytest_asyncio
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.program_logs_dao import ProgramLoggingDao

"""
File exists to end the problem with "cannot await coroutine!"
and other such nonsense irritations when trying to
set up and run a DB connection during a DAO test.

Offenders: 
1. TypeError: 'coroutine' object is not callable
"""

@pytest.mark.asyncio
async def test_plain_async_engine(plain_async_engine):
    assert isinstance(plain_async_engine, async_sessionmaker), "You need to mark @pytest_asyncio.fixture somewhere"
    log_dao = ProgramLoggingDao(plain_async_engine)
    sum_dao = ProgramSummaryDao(log_dao, plain_async_engine)

    all_summaries = await sum_dao.read_all()
    all_logs = await log_dao.read_all()

    assert all_summaries is not None
    assert all_logs is not None

    assert len(all_summaries) == 0
    assert len(all_logs) == 0