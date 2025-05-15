# test_schema_manager.py
import json
import os
import uuid

from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql import text

import time

from typing import AsyncGenerator, Optional

from activitytracker.db.database import (
    async_session_maker,
    simulation_async_engine,
    simulation_sync_engine,
)

load_dotenv()


# Add schema management for testing
class TestSchemaManager:
    """Manages PostgreSQL schemas for test isolation."""

    def __init__(self):
        self.current_schema: Optional[str] = None
        self._test_metadata_table = "test_run_metadata"

    def generate_schema_name(self, prefix="test_"):
        """Generate a unique schema name for a test run."""
        # Create a name using timestamp and random bits for uniqueness
        timestamp = int(time.time())
        random_suffix = uuid.uuid4().hex[:6]
        return f"{prefix}{timestamp}_{random_suffix}"

    async def create_schema(self, test_name: str, input_file: str | None = None) -> str:
        """Create a new schema for a test run and return its name."""
        schema_name = self.generate_schema_name()

        async with async_session_maker() as session:
            # Create the schema
            await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

            # Create metadata table in the new schema
            await session.execute(
                text(
                    f"""
                CREATE TABLE IF NOT EXISTS "{schema_name}".{self._test_metadata_table} (
                    key TEXT PRIMARY KEY,
                    value JSONB
                )
            """
                )
            )

            # Store test metadata
            await session.execute(
                text(
                    f"""
                INSERT INTO "{schema_name}".{self._test_metadata_table} (key, value)
                VALUES ('test_info', :test_info)
            """
                ),
                {
                    "test_info": json.dumps(
                        {
                            "name": test_name,
                            "input_file": input_file,
                            "created_at": str(time.time()),
                            "status": "CREATED",
                        }
                    )
                },
            )

            await session.commit()

        self.current_schema = schema_name
        return schema_name

    async def set_schema(self, schema_name: str) -> bool:
        """Set the current schema for database operations."""
        # Verify schema exists
        async with async_session_maker() as session:
            result = await session.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"
                ),
                {"schema_name": schema_name},
            )

            if result.scalar_one_or_none() is None:
                return False

        self.current_schema = schema_name
        return True

    async def mark_schema_status(self, status: str, notes: str | None = None) -> bool:
        """Update the status of the current test schema."""
        if not self.current_schema:
            return False

        async with async_session_maker() as session:
            await session.execute(
                text(
                    f"""
                UPDATE "{self.current_schema}".{self._test_metadata_table}
                SET value = jsonb_set(
                    jsonb_set(value, '{{status}}', :status::jsonb),
                    '{{completed_at}}', :completed_at::jsonb
                )
                WHERE key = 'test_info'
            """
                ),
                {
                    "status": f'"{status}"',
                    "completed_at": f'"{time.time()}"',
                },
            )

            if notes:
                await session.execute(
                    text(
                        f"""
                    UPDATE "{self.current_schema}".{self._test_metadata_table}
                    SET value = jsonb_set(value, '{{notes}}', :notes::jsonb)
                    WHERE key = 'test_info'
                """
                    ),
                    {"notes": f'"{notes}"'},
                )

            await session.commit()

        return True

    async def list_test_schemas(self):
        """List all test schemas and their metadata."""
        async with async_session_maker() as session:
            # Get all schemas with the test_ prefix
            result = await session.execute(
                text(
                    """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'test_%'
                ORDER BY schema_name
            """
                )
            )

            schemas = result.scalars().all()

            # Fetch metadata for each schema
            test_runs = []
            for schema in schemas:
                try:
                    metadata = await session.execute(
                        text(
                            f"""
                        SELECT value FROM "{schema}".{self._test_metadata_table}
                        WHERE key = 'test_info'
                    """
                        )
                    )

                    info = metadata.scalar_one_or_none()
                    test_runs.append({"schema_name": schema, "info": info})
                except Exception:
                    # Handle case where schema exists but metadata table doesn't
                    test_runs.append({"schema_name": schema, "info": None})

            return test_runs

    async def drop_schema(self, schema_name: str) -> bool:
        """Delete a test schema."""
        if self.current_schema == schema_name:
            self.current_schema = None

        async with async_session_maker() as session:
            try:
                await session.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return False


# Create a global instance of the schema manager
test_schema_manager = TestSchemaManager()


# Register for async engine (needs special handling)
@event.listens_for(sync_engine, "connect")
def set_search_path_regular(dbapi_connection, connection_record):
    """Set the search_path for newly created regular connections."""
    if test_schema_manager.current_schema:
        cursor = dbapi_connection.cursor()
        cursor.execute(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        cursor.close()


@event.listens_for(simulation_sync_engine, "connect")
def set_search_path_simulation(dbapi_connection, connection_record):
    """Set the search_path for newly created simulation connections."""
    if test_schema_manager.current_schema:
        cursor = dbapi_connection.cursor()
        cursor.execute(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        cursor.close()


def set_sync_search_path(session):
    """Set the search_path for a synchronous session."""
    if test_schema_manager.current_schema:
        session.execute(
            text(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        )


async def set_async_search_path(session):
    """Set the search_path for an async session."""
    if test_schema_manager.current_schema:
        await session.execute(
            text(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        )


# Modified get_db to include schema setting
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            # Set schema if we're in test mode
            if test_schema_manager.current_schema:
                await set_async_search_path(session)
            yield session
        finally:
            await session.close()


# Initialize database
async def init_db() -> None:
    """Initialize the database by creating all tables if they don't exist."""
    # This function is now only for initial setup, not test schemas
    pass
