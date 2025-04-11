import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, MetaData
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os


import psutil

process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)

from surveillance.src.db.dao.base_dao import BaseQueueingDao


load_dotenv()

ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

if ASYNC_TEST_DB_URL is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")


# Helper function to check open connections
async def get_checkedout_conns(engine):
    """Get number of checked-out connections from the pool"""
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync_conn: sync_conn.engine.pool.checkedout())


# At the top of your test file
print("MODULE LOAD - Checking for existing connections")

async def check_initial_connections():
    engine = create_async_engine(ASYNC_TEST_DB_URL)
    conns = await get_checkedout_conns(engine)
    print(f"INITIAL CONNECTION COUNT: {conns}")
    if conns > 0:
        import traceback
        print("STACK TRACE AT MODULE LOAD:")
        traceback.print_stack()

# Run the async function
asyncio.run(check_initial_connections())

# Create a test model
Base = declarative_base()

class JustForTestsModel(Base):
    __tablename__ = "test_cleanup_model"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now())


# Create a test DAO that inherits from BaseQueueingDao
class JustForTestsDao(BaseQueueingDao):
    """Simple DAO implementation for testing the BaseQueueingDao cleanup functionality"""
    def __init__(self, async_session_maker, batch_size=10, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker, batch_size=batch_size, flush_interval=flush_interval)
    
    async def create_test_item(self, name, description=""):
        """Create a test item and queue it"""
        item = JustForTestsModel(name=name, description=description)
        await self.queue_item(item, JustForTestsModel)
        return item


DEFAULT_BOOTSTRAP_CONNECTION = 1


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Set up a test database"""
    # Create engine and sessionmaker
    engine = create_async_engine(ASYNC_TEST_DB_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine, async_session
    
    # Clean up - drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_cleanup_properly_closes_connections(test_db):
    engine, async_session = test_db
    
    # Get initial connection count (may be 1)
    initial_conns = await get_checkedout_conns(engine)
    print(f"Initial connections: {initial_conns}")
    
    # Create a DAO instance
    test_dao = JustForTestsDao(async_session, batch_size=5, flush_interval=1)
    
    # Queue some items
    for i in range(10):
        await test_dao.create_test_item(f"Test {i}", f"Description {i}")
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Get connections during processing
    processing_conns = await get_checkedout_conns(engine)
    print(f"Connections during processing: {processing_conns}")
    
    # Call cleanup
    await test_dao.cleanup()
    await asyncio.sleep(1)
    
    # Verify we're back to the initial connection count
    final_conns = await get_checkedout_conns(engine)
    assert final_conns == initial_conns, f"Expected {initial_conns} connections after cleanup, got {final_conns}"


@pytest.mark.asyncio
async def test_multiple_daos_cleanup(test_db):
    """Test cleanup with multiple DAOs using the same connection pool"""
    engine, async_session = test_db
    
    # Create multiple DAO instances
    test_dao1 = JustForTestsDao(async_session, batch_size=3, flush_interval=1)
    test_dao2 = JustForTestsDao(async_session, batch_size=3, flush_interval=1)
    test_dao3 = JustForTestsDao(async_session, batch_size=3, flush_interval=1)
    
    # Queue items to all DAOs to trigger background tasks
    for i in range(5):
        await test_dao1.create_test_item(f"DAO1 Test {i}")
        await test_dao2.create_test_item(f"DAO2 Test {i}")
        await test_dao3.create_test_item(f"DAO3 Test {i}")
    
    # Wait for some processing to happen
    await asyncio.sleep(2)
    
    # Check connections during processing
    processing_conns = await get_checkedout_conns(engine)
    print(f"Connections during processing: {processing_conns}")
    
    # Clean up all DAOs
    await test_dao1.cleanup()
    await test_dao2.cleanup()
    await test_dao3.cleanup()
    
    # Wait for cleanup to complete fully
    await asyncio.sleep(1)
    
    # Verify all connections are closed
    final_conns = await get_checkedout_conns(engine)
    assert final_conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Expected 0 connections after cleanup, got {final_conns}"


@pytest.mark.asyncio
async def test_async_context_manager(test_db):
    """Test the async context manager protocol of BaseQueueingDao"""
    engine, async_session = test_db
    
    # Use the DAO as an async context manager
    async with JustForTestsDao(async_session, batch_size=3, flush_interval=1) as test_dao:
        for i in range(5):
            await test_dao.create_test_item(f"CM Test {i}")
        
        # Wait for some processing
        await asyncio.sleep(2)
    
    # Context manager should have called cleanup automatically
    # Wait a moment for any async cleanup to complete
    await asyncio.sleep(1)
    
    # Verify connections are closed
    final_conns = await get_checkedout_conns(engine)
    assert final_conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Expected 0 connections after context manager exit, got {final_conns}"


@pytest.mark.asyncio
async def test_cleanup_with_pending_items(test_db):
    """Test cleanup works properly with items still in the queue"""
    engine, async_session = test_db
    
    # Create DAO with slow flush interval
    test_dao = JustForTestsDao(async_session, batch_size=10, flush_interval=1)
    
    # Queue a bunch of items that won't flush immediately
    for i in range(20):
        await test_dao.create_test_item(f"Pending Test {i}")
    
    # Call cleanup immediately without waiting
    # This should handle pending items properly
    await test_dao.cleanup()
    
    # Verify connections are closed
    final_conns = await get_checkedout_conns(engine)
    assert final_conns == DEFAULT_BOOTSTRAP_CONNECTION, f"Expected 0 connections after cleanup with pending items, got {final_conns}"
    
    # Verify data was saved properly despite early cleanup
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(JustForTestsModel).where(JustForTestsModel.name.like("Pending Test%")))
        items = result.scalars().all()
        assert len(items) == 20, f"Expected 20 items saved, found {len(items)}"



