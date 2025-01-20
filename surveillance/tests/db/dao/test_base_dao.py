

# import pytest
# import pytest_asyncio
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import declarative_base
# from sqlalchemy import Column, Integer, String
# import asyncio
# from unittest.mock import Mock, patch
# from datetime import datetime

# # Import your BaseQueueingDao
# from src.db.dao.base_dao import BaseQueueingDao

# # Create a test model
# Base = declarative_base()


# class TestModel(Base):
#     __tablename__ = 'test_model'
#     id = Column(Integer, primary_key=True)
#     value = Column(String)

#     def __repr__(self):
#         return f"TestModel(id={self.id}, value='{self.value}')"

# # Fixtures


# @pytest_asyncio.fixture
# async def async_engine():
#     engine = create_async_engine('sqlite+aiosqlite:///:memory:')
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield engine
#     await engine.dispose()


# @pytest_asyncio.fixture
# async def db_session(async_engine):
#     async with AsyncSession(async_engine) as session:
#         yield session


# @pytest_asyncio.fixture
# def dao(db_session):
#     return BaseQueueingDao(db_session, batch_size=2, flush_interval=1)

# # Tests


# @pytest.mark.asyncio
# async def test_queue_item_starts_processing(dao):
#     """Test that queueing an item starts processing if not already started"""
#     assert not dao.processing
#     test_item = TestModel(value="test1")
#     await dao.queue_item(test_item)
#     assert dao.processing


# @pytest.mark.asyncio
# async def test_batch_processing(dao):
#     """Test that items are processed in batches"""
#     test_items = [
#         TestModel(value=f"test{i}")
#         for i in range(3)
#     ]

#     for item in test_items:
#         await dao.queue_item(item)

#     # Wait for processing
#     await asyncio.sleep(2)

#     # Check items were saved
#     result = await dao.db.execute("SELECT COUNT(*) FROM test_model")
#     count = (await result.first())[0]
#     assert count == 3


# @pytest.mark.asyncio
# async def test_batch_size_respected(dao):
#     """Test that batch size limit is respected"""
#     test_items = [
#         TestModel(value=f"test{i}")
#         for i in range(5)
#     ]

#     processed_batches = []

#     # Mock _save_batch to track batch sizes
#     original_save_batch = dao._save_batch

#     async def mock_save_batch(batch):
#         processed_batches.append(len(batch))
#         await original_save_batch(batch)

#     dao._save_batch = mock_save_batch

#     for item in test_items:
#         await dao.queue_item(item)

#     # Wait for processing
#     await asyncio.sleep(3)

#     # Check that no batch exceeded the batch size
#     assert all(size <= dao.batch_size for size in processed_batches)


# @pytest.mark.asyncio
# async def test_error_handling(dao):
#     """Test error handling during batch processing"""
#     test_item = TestModel(value="test1")

#     # Mock _save_batch to raise an exception
#     async def mock_save_batch(batch):
#         raise Exception("Test error")

#     dao._save_batch = mock_save_batch

#     # Should not raise exception
#     await dao.queue_item(test_item)
#     await asyncio.sleep(1)
#     assert True  # If we get here, the error was handled


# @pytest.mark.asyncio
# async def test_flush_interval(dao):
#     """Test that items are flushed after the flush interval"""
#     test_item = TestModel(value="test1")
#     await dao.queue_item(test_item)

#     # Wait less than flush interval
#     await asyncio.sleep(0.5)
#     result = await dao.db.execute("SELECT COUNT(*) FROM test_model")
#     count_before = (await result.first())[0]

#     # Wait for flush interval
#     await asyncio.sleep(1)
#     result = await dao.db.execute("SELECT COUNT(*) FROM test_model")
#     count_after = (await result.first())[0]

#     assert count_before == 0
#     assert count_after == 1


# @pytest.mark.asyncio
# async def test_type_checking(dao):
#     """Test that items are checked for correct type when specified"""
#     class WrongType:
#         pass

#     test_item = TestModel(value="test1")
#     wrong_item = WrongType()

#     # Should work with correct type
#     await dao.queue_item(test_item, TestModel)

#     # Should raise ValueError with wrong type
#     with pytest.raises(ValueError):
#         await dao.queue_item(wrong_item, TestModel)


# @pytest.mark.asyncio
# async def test_queue_empty_handling(dao):
#     """Test handling of empty queue"""
#     test_item = TestModel(value="test1")
#     await dao.queue_item(test_item)

#     # Wait for processing
#     await asyncio.sleep(2)

#     # Queue should be empty but processing should continue
#     assert dao.queue.empty()
#     assert dao.processing
