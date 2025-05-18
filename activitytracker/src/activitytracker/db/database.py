# database.py
import os

from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from typing import AsyncGenerator

load_dotenv()

SYNCHRONOUS_DB_URL = os.getenv("SYNCHRONOUS_DB_URL")

ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL")


if SYNCHRONOUS_DB_URL is None:
    raise ValueError("Failed to load system power table URL")
if ASYNC_DB_URL is None:
    raise ValueError("Failed to load SqlAlchemy database URL")


sync_engine = create_engine(SYNCHRONOUS_DB_URL)


async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,  # Set to True for SQL query logging
)


regular_session_maker = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)

# Create async session maker
async_session_maker = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Dependency for FastAPI endpoints


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables if they don't exist."""
    async with async_engine.begin() as conn:
        pass
        # No longer doing automatic create_all
        # as it takes the db out of sync with Alembic
        # await conn.run_sync(Base.metadata.create_all)
