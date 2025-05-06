# # Deleted April 20, 2025
# from surveillance.db.dao.base_dao import BaseQueueingDao
# import pytest
# import pytest_asyncio
# import asyncio
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# from sqlalchemy import Column, Integer, String, Text, DateTime, Table, MetaData
# from sqlalchemy.orm import declarative_base
# from datetime import datetime, timedelta

# from dotenv import load_dotenv
# import os


# import psutil

# process = psutil.Process()
# open_files = process.open_files()
# num_open_files = len(open_files)


# load_dotenv()

# ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
#     'ASYNC_TEST_DB_URL')

# if ASYNC_TEST_DB_URL is None:
#     raise ValueError("TEST_DB_STRING environment variable is not set")


# # Helper function to check open connections
# async def get_checkedout_conns(engine):
#     """Get number of checked-out connections from the pool"""
#     async with engine.connect() as conn:
#         return await conn.run_sync(lambda sync_conn: sync_conn.engine.pool.checkedout())


# # At the top of your test file
# print("MODULE LOAD - Checking for existing connections")


# async def check_initial_connections():
#     engine = create_async_engine(ASYNC_TEST_DB_URL)
#     conns = await get_checkedout_conns(engine)
#     print(f"INITIAL CONNECTION COUNT: {conns}")
#     if conns > 0:
#         import traceback
#         print("STACK TRACE AT MODULE LOAD:")
#         traceback.print_stack()

# # Run the async function
# asyncio.run(check_initial_connections())

# # Create a test model
# Base = declarative_base()


# class JustForTestsModel(Base):
#     __tablename__ = "test_cleanup_model"

#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), nullable=False)
#     description = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.now())


# # Create a test DAO that inherits from BaseQueueingDao
# class JustForTestsDao(BaseQueueingDao):
#     """Simple DAO implementation for testing the BaseQueueingDao cleanup functionality"""

#     def __init__(self, async_session_maker, batch_size=10, flush_interval=1):
#         super().__init__(async_session_maker=async_session_maker,
#                          batch_size=batch_size, flush_interval=flush_interval)

#     async def create_test_item(self, name, description=""):
#         """Create a test item and queue it"""
#         item = JustForTestsModel(name=name, description=description)
#         await self.queue_item(item, JustForTestsModel)
#         return item


# DEFAULT_BOOTSTRAP_CONNECTION = 1


# @pytest_asyncio.fixture(scope="function")
# async def test_db():
#     """Set up a test database"""
#     pass  # Removed


# @pytest.mark.asyncio
# async def test_cleanup_properly_closes_connections(test_db):
#     pass


# @pytest.mark.asyncio
# async def test_multiple_daos_cleanup(test_db):
#     """Test cleanup with multiple DAOs using the same connection pool"""
#     pass


# @pytest.mark.asyncio
# async def test_async_context_manager(test_db):
#     """Test the async context manager protocol of BaseQueueingDao"""
#     pass


# @pytest.mark.asyncio
# async def test_cleanup_with_pending_items(test_db):
#     """Test cleanup works properly with items still in the queue"""
#     pass
