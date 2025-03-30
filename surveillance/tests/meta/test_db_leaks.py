import pytest
import subprocess
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


suspicious_file0 = "tests/db/dao/test_program_dao.py"
suspicious_file1 = "tests/db/dao/test_program_summary_dao.py"
suspicious_file3 = "tests/db/dao/test_system_status_dao.py"
suspicious_file4 = "tests/db/dao/test_timeline_entry_dao.p"

gooder1 = "tests/db/dao/test_chrome_summary_dao.py"
gooder2 = "tests/db/dao/test_keyboard_dao.py"
gooder3 = "tests/db/dao/test_logging_dao.py"
gooder4 = "tests/db/dao/test_mouse_dao.py"
# suspicious_files = [suspicious_file1,suspicious_file2,suspicious_file3,suspicious_file4,suspicious_file0]

@pytest.mark.asyncio
async def test_db_leaks2():
    # Import the test function directly
    from tests.db.dao.test_session_integrity_dao import test_find_orphans, full_test_environment
    
    # Run the test directly
    await test_find_orphans(await full_test_environment())
    
    # Get a fresh engine to check connections
    engine = create_async_engine(ASYNC_TEST_DB_URL)
    open_conns = await get_checkedout_conns(engine)
    assert open_conns == 0

@pytest.mark.asyncio
async def test_db_leaks(async_engine_and_asm):
    engine, _ = async_engine_and_asm
    """Runs a test file and checks for leaked DB connections."""
    
    # Run Pytest on the target test file

    # result0 = subprocess.run(["pytest", suspicious_file0], capture_output=True, text=True)
    # result1 = subprocess.run(["pytest", suspicious_file1], capture_output=True, text=True)
    suspicious_file2 = "tests/db/dao/test_session_integrity_dao.py"   #####
    result2 = subprocess.run(["pytest", suspicious_file2], capture_output=True, text=True)
    # result3 = subprocess.run(["pytest", suspicious_file3], capture_output=True, text=True)
    # result4 = subprocess.run(["pytest", suspicious_file4], capture_output=True, text=True)
    # result4 = subprocess.run(["pytest", gooder4], capture_output=True, text=True)
    
    # Print test output (optional, for debugging)
    # print(result.stdout)
    # print(result.stderr)

    # Check for leaked DB connections
    open_conns = await get_checkedout_conns(engine)
    assert open_conns == 0, f"Leaked {open_conns} DB connections detected!"


# @pytest.mark.asyncio
# async def test_db_leaks_sqlite(async_in_mem_engine):
#     """Runs a test file and checks for leaked DB connections."""
    
#     # Run Pytest on the target test file
#     result = subprocess.run(["pytest", "tests/dao/test_example.py"], capture_output=True, text=True)
    
#     # Print test output (optional, for debugging)
#     print(result.stdout)
#     print(result.stderr)

#     # Check for leaked DB connections
#     open_conns = await get_checkedout_conns(async_in_mem_engine)
#     assert open_conns == 0, f"Leaked {open_conns} DB connections detected!"



# @pytest.mark.asyncio
# async def test_db_leak_debug(async_engine_and_asm):
#     engine, _ = async_engine_and_asm

#     before_conns = await get_checkedout_conns(engine)
#     logger.debug(f"Checked-out connections before test: {before_conns}")

#     result = subprocess.run(["pytest", "tests/db/dao/test_program_summary_dao.py"], capture_output=True, text=True)

#     after_conns = await get_checkedout_conns(engine)
#     logger.debug(f"Checked-out connections after test: {after_conns}")

#     assert after_conns == 0, f"Leaked {after_conns} DB connections detected!"