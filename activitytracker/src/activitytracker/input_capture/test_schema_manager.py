# test_schema_manager.py
import json
import os
import uuid

from dotenv import load_dotenv

from sqlalchemy import event
from sqlalchemy.sql import text

import time

from typing import Generator, Optional

from activitytracker.config.definitions import program_environment
from activitytracker.db.database import (
    simulation_regular_session_maker,
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

    def create_schema(self, test_name: str, input_file: str | None = None) -> str:
        """Create a new schema for a test run and return its name."""
        schema_name = self.generate_schema_name()

        test_info = json.dumps(
            {
                "name": test_name,
                "input_file": input_file,
                "created_at": str(time.time()),
                "status": "CREATED",
            }
        )

        with simulation_regular_session_maker() as session:
            # Create the schema
            session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

            # Create metadata table in the new schema
            session.execute(
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
            session.execute(
                text(
                    f"""
                INSERT INTO "{schema_name}".{self._test_metadata_table} (key, value)
                VALUES ('test_info', :test_info)
            """
                ),
                {"test_info": test_info},
            )

            session.commit()

        self.current_schema = schema_name
        return schema_name

    def set_schema(self, schema_name: str) -> bool:
        """Set the current schema for database operations."""
        # Verify schema exists
        with simulation_regular_session_maker() as session:
            result = session.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"
                ),
                {"schema_name": schema_name},
            )

            if result.scalar_one_or_none() is None:
                return False

        self.current_schema = schema_name
        return True

    def mark_schema_status(self, status: str, notes: str | None = None) -> bool:
        """Update the status of the current test schema."""
        if not self.current_schema:
            return False

        with simulation_regular_session_maker() as session:
            session.execute(
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
                session.execute(
                    text(
                        f"""
                    UPDATE "{self.current_schema}".{self._test_metadata_table}
                    SET value = jsonb_set(value, '{{notes}}', :notes::jsonb)
                    WHERE key = 'test_info'
                """
                    ),
                    {"notes": f'"{notes}"'},
                )

            session.commit()

        return True

    def list_test_schemas(self):
        """List all test schemas and their metadata."""
        with simulation_regular_session_maker() as session:
            # Get all schemas with the test_ prefix
            result = session.execute(
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
                    metadata = session.execute(
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

    def drop_schema(self, schema_name: str) -> bool:
        """Delete a test schema."""
        if self.current_schema == schema_name:
            self.current_schema = None

        with simulation_regular_session_maker() as session:
            try:
                session.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
                session.commit()
                return True
            except Exception:
                session.rollback()
                return False


# Create a global instance
test_schema_manager = TestSchemaManager()

if program_environment.data_capture_session:
    print("Capture")


# SQLAlchemy connection event to set search_path
def register_connection_event(engine):
    """Register a connection event listener that sets the search_path for the given engine."""
    from sqlalchemy import event

    def set_search_path(dbapi_connection, connection_record):
        """Set the search_path for newly created connections."""
        if test_schema_manager.current_schema:
            cursor = dbapi_connection.cursor()
            cursor.execute(
                f'SET search_path TO "{test_schema_manager.current_schema}", public'
            )
            cursor.close()

    # Register the event listener directly
    event.listen(engine, "connect", set_search_path)

    return None  # Optional: can return None or the engine for method chaining


if program_environment.development:
    # No need
    print("Passing on connection registration")
else:
    register_connection_event(simulation_sync_engine)


def set_sync_search_path(session):
    """Set the search_path for a synchronous session."""
    if test_schema_manager.current_schema:
        session.execute(
            text(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        )


# Async version for set_schema_path
async def set_async_search_path(session):
    """Set the search_path for an async session."""
    if test_schema_manager.current_schema:
        await session.execute(
            text(f'SET search_path TO "{test_schema_manager.current_schema}", public')
        )
