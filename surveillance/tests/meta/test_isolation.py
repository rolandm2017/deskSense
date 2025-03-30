# test_isolation.py
import pytest
import asyncio
from sqlalchemy.pool import NullPool  
from sqlalchemy.ext.asyncio import create_async_engine

from dotenv import load_dotenv
import os



load_dotenv()

ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

if ASYNC_TEST_DB_URL is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")

DEFAULT_BOOTSTRAP_CONNECTION = 1


async def get_checkedout_conns(engine):
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync_conn: sync_conn.engine.pool.checkedout())

@pytest.mark.asyncio
async def test_connection_count():
    engine = create_async_engine(ASYNC_TEST_DB_URL)
    conns = await get_checkedout_conns(engine)
    assert conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Found {conns} connections"