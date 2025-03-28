import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock


from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy import text

from src.db.models import Base
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
async def test_plain_async_engine(plain_async_engine_and_asm):
    engine, asm = plain_async_engine_and_asm

    assert isinstance(asm, async_sessionmaker), "You need to mark @pytest_asyncio.fixture somewhere if you see this error"

    # Try to use it
    log_dao = ProgramLoggingDao(asm)
    sum_dao = ProgramSummaryDao(log_dao, asm)


    all_summaries = await sum_dao.read_all()
    all_logs = await log_dao.read_all()

    assert all_summaries is not None
    assert all_logs is not None

    assert len(all_logs) == 0, "Should be nothing in a brand new db"
    assert len(all_summaries) == 0, "Should be nothing in a brand new db"

@pytest.mark.asyncio
async def test_reset_db(plain_async_engine_and_asm):
    engine, _ = plain_async_engine_and_asm

    assert isinstance(engine, AsyncEngine)
    assert hasattr(engine, 'connect') and callable(getattr(engine, 'connect')), "Engine lacked connect method!"

    async def reset_database(something):
        async with something.connect() as conn:
            # Terminate existing connections more safely
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))

            # Drop and recreate database
            await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
            await conn.execute(text("CREATE DATABASE dsTestDb"))
        return True

    result = await reset_database(engine)

    assert result is True, "The reset_database method failed or threw an error"
  
@pytest.mark.asyncio
async def test_sqlite(async_db_session_in_mem):
      # Try to use it
    assert isinstance(async_db_session_in_mem, async_sessionmaker)
    log_dao = ProgramLoggingDao(async_db_session_in_mem)
    sum_dao = ProgramSummaryDao(log_dao, async_db_session_in_mem)

    all_summaries = await sum_dao.read_all()
    all_logs = await log_dao.read_all()

    assert all_summaries is not None
    assert all_logs is not None

    for v in all_summaries:
        print(v)
    assert len(all_summaries) == 0
    assert len(all_logs) == 0
