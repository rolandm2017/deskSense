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
    for v in all_logs:
        print(v)
    for v in all_summaries:
        print(v)
    assert isinstance(all_summaries, list)
    assert isinstance(all_logs, list)

  
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


    for v in all_logs:
        print(v)
    for v in all_summaries:
        print(v)
    assert len(all_summaries) == 0
    assert len(all_logs) == 0


# ERROR tests/db/dao/test_logging_dao.py::test_start_session - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_logging_dao.py::test_find_session - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_logging_dao.py::test_push_window_ahead - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_logging_dao.py::test_push_window_error - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_logging_dao.py::test_finalize_log_error - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_dao.py::TestProgramDao::test_create_happy_path - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_create_if_new_else_update_new_entry - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_create_if_new_else_update_existing_entry - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_read_day - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_read_all - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_read_row_for_program - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_delete - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_delete_nonexistent - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_several_consecutive_writes - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_program_summary_dao.py::TestProgramSummaryDao::test_series_of_database_operations - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_session_integrity_dao.py::test_find_orphans - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_system_status_dao.py::test_read_latest_status - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_system_status_dao.py::test_create_different_statuses - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_system_status_dao.py::test_read_latest_shutdown - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_system_status_dao.py::test_read_latest_status_returns_none_if_no_statuses - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...
# ERROR tests/db/dao/test_system_status_dao.py::test_read_latest_shutdown_returns_none_if_no_statuses - sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.ObjectInUseError'>: database "dstestdb" is being accessed by oth...