# database.py
import os

from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from typing import AsyncGenerator, Generator

from activitytracker.config.definitions import program_environment
from activitytracker.input_capture.test_schema_manager import 
from activitytracker.util.console_logger import ConsoleLogger


# Modified get_db to include schema setting
def get_db() -> Generator[Session, None, None]:
    if program_environment.development:
        with regular_session_maker() as session:
            try:
                yield session
            finally:
                session.close()
    else:
        # Use get_simulation_db directly if in data capture session
        yield from get_simulation_db()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    if program_environment.development:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        # Use get_async_simulation_db directly
        async for session in get_async_simulation_db():
            yield session
