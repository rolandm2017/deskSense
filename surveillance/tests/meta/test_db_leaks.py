import pytest
import subprocess
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import inspect
from dotenv import load_dotenv
import os


import logging

load_dotenv()

ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

if ASYNC_TEST_DB_URL is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")

logger = logging.getLogger(__name__)

async def get_checkedout_conns(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync_conn: sync_conn.engine.pool.checkedout())


DEFAULT_BOOTSTRAP_CONNECTION = 1
# ALLEGEDLY: "When you create an engine in SQLAlchemy with asyncpg as the driver, SQLAlchemy opens an initial bootstrap connection."

suspicious_file0 = "tests/db/dao/test_program_dao.py"
suspicious_file1 = "tests/db/dao/test_program_summary_dao.py"
suspicious_file2 = "tests/db/dao/test_session_integrity_dao.py"   #####

suspicious_file3 = "tests/db/dao/test_system_status_dao.py"
suspicious_file4 = "tests/db/dao/test_timeline_entry_dao.p"

gooder1 = "tests/db/dao/test_chrome_summary_dao.py"
gooder2 = "tests/db/dao/test_keyboard_dao.py"
gooder3 = "tests/db/dao/test_logging_dao.py"
gooder4 = "tests/db/dao/test_mouse_dao.py"
# suspicious_files = [suspicious_file1,suspicious_file2,suspicious_file3,suspicious_file4,suspicious_file0]
@pytest.mark.asyncio
async def test_db_leaks3(async_engine_and_asm):
    """Test that session_integrity_dao tests don't leak connections."""
    engine, _ = async_engine_and_asm
    
    # Get initial connection count
    initial_conns = await get_checkedout_conns(engine)
    
    # Run the test programmatically
    import pytest
    result = pytest.main(['-xvs', 'tests/db/dao/test_session_integrity_dao.py::test_find_orphans'])
    
    # Wait a moment for any async cleanup to complete
    await asyncio.sleep(1)
    
    # Check for leaked connections
    final_conns = await get_checkedout_conns(engine)
    assert final_conns == initial_conns, f"Leaked {final_conns - initial_conns} DB connections detected!"
    assert initial_conns == DEFAULT_BOOTSTRAP_CONNECTION  # Mystery connection
    assert final_conns == DEFAULT_BOOTSTRAP_CONNECTION # Mystery connection



@pytest.mark.asyncio
async def test_db_leaks(async_engine_and_asm):
    engine, _ = async_engine_and_asm
    """Runs a test file and checks for leaked DB connections."""
    
    # Run Pytest on the target test file

    # result0 = subprocess.run(["pytest", suspicious_file0], capture_output=True, text=True)
    # result1 = subprocess.run(["pytest", suspicious_file1], capture_output=True, text=True)
    result2 = subprocess.run(["pytest", suspicious_file2], capture_output=True, text=True)
    # result3 = subprocess.run(["pytest", suspicious_file3], capture_output=True, text=True)
    # result4 = subprocess.run(["pytest", suspicious_file4], capture_output=True, text=True)
    # result4 = subprocess.run(["pytest", gooder4], capture_output=True, text=True)
    
    # Print test output (optional, for debugging)
    # print(result.stdout)
    # print(result.stderr)

    # Check for leaked DB connections
    open_conns = await get_checkedout_conns(engine)
    assert open_conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Leaked {open_conns} DB connections detected!"


@pytest.mark.asyncio
async def test_db_leaks_sqlite(async_db_session_in_mem):
    """Runs a test file and checks for leaked DB connections."""
    engine, asm = async_db_session_in_mem
    
    # Run Pytest on the target test file
    result = subprocess.run(["pytest", suspicious_file2], capture_output=True, text=True)
    
    # Print test output (optional, for debugging)
    print(result.stdout)
    print(result.stderr)

    # Check for leaked DB connections
    open_conns = await get_checkedout_conns(engine)
    assert open_conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Leaked {open_conns} DB connections detected!"



# @pytest.mark.asyncio
# async def test_db_leak_debug(async_engine_and_asm):
#     engine, _ = async_engine_and_asm

#     before_conns = await get_checkedout_conns(engine)
#     logger.debug(f"Checked-out connections before test: {before_conns}")

#     result = subprocess.run(["pytest", "tests/db/dao/test_program_summary_dao.py"], capture_output=True, text=True)

#     after_conns = await get_checkedout_conns(engine)
#     logger.debug(f"Checked-out connections after test: {after_conns}")

#     assert after_conns == 0, f"Leaked {after_conns} DB connections detected!"