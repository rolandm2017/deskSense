# database.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import AsyncGenerator
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

SYNCHRONOUS_DB_URL = os.getenv("SYSTEM_TABLE_DB_URL")

if SQLALCHEMY_DATABASE_URL is None:
    raise ValueError("Failed to load SqlAlchemy database URL")

if SYNCHRONOUS_DB_URL is None:
    raise ValueError("Failed to load system power table URL")

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
)

sync_engine = create_engine(SYNCHRONOUS_DB_URL)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

shutdown_session_maker = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
