# test_run_manager.py
import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

import time
from datetime import datetime, timedelta

from typing import Any, Dict, List, Optional

from activitytracker.config.definitions import program_environment
from activitytracker.db.database import async_session_maker


def get_timestamp_string():
    """Returns current time as YYYY-MM-DD_HH-MM-SS string for file naming."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

    # TODO: Should be single source of truth about the enviromment being capture
    # SO it needs to go into the database.py file, OR the db.py file needs to show up here
    # TODO: I need to show that i got the inputs and the outputs
    # TODO: I need the db schema to increment automatically

    # TODO: Get the database setup


class TestRunManager:
    """Manages test runs and their execution within isolated database schemas."""

    def __init__(self, schema_manager=None):
        """Initialize the test run manager.

        Args:
            schema_manager: Optional schema manager instance to use. If None,
                            a reference to the global test_schema_manager will be used.
        """
        # Import here to avoid circular imports
        from .test_schema import test_schema_manager

        self.run_id = self.generate_run_id()
        self.session_active = program_environment.data_capture_session

        self.schema_manager = schema_manager or test_schema_manager
        self.current_run_id: Optional[str] = None
        self.metadata_table = "test_run_metadata"
        self.results_table = "test_run_results"
        self.filename = self.make_filename()

    def make_filename(self):
        logs_dir = os.path.join(".", "logs")

        os.makedirs(logs_dir, exist_ok=True)

        return os.path.join(logs_dir, "input_from_" + get_timestamp_string() + ".json")

    def generate_run_id(self) -> str:
        """Generate a unique ID for a test run."""
        timestamp = int(time.time())
        random_suffix = uuid.uuid4().hex[:6]
        return f"run_{timestamp}_{random_suffix}"

    async def initialize(
        self, input_capture_file: str, test_name: str = "Activity Tracking Test"
    ) -> str:
        """Initialize a new test run with a dedicated schema.

        Args:
            input_capture_file: Path to the file containing captured system inputs
            test_name: Name for this test run

        Returns:
            The unique run ID for this test
        """
        # Create a new test schema
        schema_name = await self.schema_manager.create_schema(
            test_name=test_name, input_file=input_capture_file
        )

        # Generate run ID
        run_id = self.generate_run_id()
        self.current_run_id = run_id

        # Create test run tables in the schema
        async with async_session_maker() as session:
            # Set search path
            await self.schema_manager.set_schema(schema_name)

            # Create results table
            await session.execute(
                text(
                    f"""
                CREATE TABLE IF NOT EXISTS "{schema_name}".{self.results_table} (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    event_type TEXT NOT NULL,
                    data JSONB,
                    source TEXT,
                    status TEXT DEFAULT 'SUCCESS'
                )
            """
                )
            )

            # Store run metadata
            await session.execute(
                text(
                    f"""
                INSERT INTO "{schema_name}".{self.metadata_table} (key, value)
                VALUES ('run_info', :run_info)
            """
                ),
                {
                    "run_info": {
                        "id": run_id,
                        "schema_name": schema_name,
                        "input_file": input_capture_file,
                        "started_at": time.time(),
                        "status": "INITIALIZED",
                    }
                },
            )

            await session.commit()

        return run_id

    async def record_event(
        self, event_type: str, data: Dict[str, Any], source: str = "test_runner"
    ) -> int:
        """Record a test event in the current run.

        Args:
            event_type: Type of event (e.g., "INPUT_CAPTURED", "OUTPUT_VERIFIED")
            data: Dictionary of event data
            source: Source component that generated this event

        Returns:
            The ID of the inserted event record
        """
        if not self.schema_manager.current_schema:
            raise ValueError("No active test schema. Call initialize() first")

        async with async_session_maker() as session:
            # Set search path
            await self.schema_manager.set_async_search_path(session)

            # Insert the event
            result = await session.execute(
                text(
                    f"""
                INSERT INTO {self.results_table} (event_type, data, source)
                VALUES (:event_type, :data, :source)
                RETURNING id
            """
                ),
                {"event_type": event_type, "data": data, "source": source},
            )

            event_id = result.scalar_one()
            await session.commit()

            return event_id

    async def freeze(self, status: str, notes: str | None = None) -> bool:
        """Mark the current test run as complete with a status.

        Args:
            status: Final status of the test run (e.g., "PASSED", "FAILED")
            notes: Optional notes about the test outcome

        Returns:
            True if successful, False otherwise
        """
        if not self.schema_manager.current_schema or not self.current_run_id:
            return False

        # Update both the schema metadata and run metadata
        schema_updated = await self.schema_manager.mark_schema_status(status, notes)

        async with async_session_maker() as session:
            # Set search path
            await self.schema_manager.set_async_search_path(session)

            # Update run metadata
            try:
                await session.execute(
                    text(
                        f"""
                    UPDATE {self.metadata_table}
                    SET value = jsonb_set(
                        jsonb_set(
                            jsonb_set(value, '{{status}}', :status::jsonb),
                            '{{completed_at}}', :completed_at::jsonb
                        ),
                        '{{duration}}', :duration::jsonb
                    )
                    WHERE key = 'run_info'
                """
                    ),
                    {
                        "status": f'"{status}"',
                        "completed_at": f'"{time.time()}"',
                        "duration": f'"{time.time() - float(await self._get_start_time())}"',
                    },
                )

                if notes:
                    await session.execute(
                        text(
                            f"""
                        UPDATE {self.metadata_table}
                        SET value = jsonb_set(value, '{{notes}}', :notes::jsonb)
                        WHERE key = 'run_info'
                    """
                        ),
                        {"notes": f'"{notes}"'},
                    )

                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"Error freezing test run: {e}")
                return False

    async def _get_start_time(self) -> str:
        """Helper to retrieve the start time of the current run."""
        async with async_session_maker() as session:
            # Set search path
            await self.schema_manager.set_async_search_path(session)

            result = await session.execute(
                text(
                    f"""
                SELECT value->>'started_at' FROM {self.metadata_table}
                WHERE key = 'run_info'
            """
                )
            )

            start_time = result.scalar_one_or_none() or "0"
            return start_time

    async def get_run_details(self, run_id: str | None = None) -> Optional[Dict[str, Any]]:
        """Get details about a specific test run.

        Args:
            run_id: The run ID to fetch details for, or current run if None

        Returns:
            Dictionary with run details or None if not found
        """
        run_id = run_id or self.current_run_id
        if not run_id:
            return None

        async with async_session_maker() as session:
            # Find the schema containing this run
            schemas = await self.schema_manager.list_test_schemas()

            for schema in schemas:
                schema_name = schema["schema_name"]

                # Check if this schema contains our run
                try:
                    result = await session.execute(
                        text(
                            f"""
                        SELECT value FROM "{schema_name}".{self.metadata_table}
                        WHERE key = 'run_info' AND value->>'id' = :run_id
                    """
                        ),
                        {"run_id": run_id},
                    )

                    run_info = result.scalar_one_or_none()
                    if run_info:
                        # Get event summary
                        events_result = await session.execute(
                            text(
                                f"""
                            SELECT 
                                COUNT(*) as total_events,
                                COUNT(*) FILTER (WHERE status = 'SUCCESS') as success_events,
                                COUNT(*) FILTER (WHERE status != 'SUCCESS') as failed_events
                            FROM "{schema_name}".{self.results_table}
                        """
                            )
                        )

                        events_summary = events_result.mappings().one()

                        return {
                            "run_id": run_id,
                            "schema_name": schema_name,
                            "info": run_info,
                            "events": dict(events_summary),
                        }
                except Exception:
                    continue

            return None

    async def list_runs(self) -> List[Dict[str, Any]]:
        """List all test runs across all schemas.

        Returns:
            List of dictionaries with run information
        """
        runs = []
        schemas = await self.schema_manager.list_test_schemas()

        async with async_session_maker() as session:
            for schema in schemas:
                schema_name = schema["schema_name"]

                try:
                    result = await session.execute(
                        text(
                            f"""
                        SELECT value FROM "{schema_name}".{self.metadata_table}
                        WHERE key = 'run_info'
                    """
                        )
                    )

                    run_info = result.scalar_one_or_none()
                    if run_info:
                        runs.append(
                            {
                                "run_id": run_info.get("id", "unknown"),
                                "schema_name": schema_name,
                                "status": run_info.get("status", "UNKNOWN"),
                                "input_file": run_info.get("input_file"),
                                "started_at": run_info.get("started_at"),
                                "completed_at": run_info.get("completed_at"),
                            }
                        )
                except Exception:
                    # Skip schemas without proper metadata
                    continue

        return runs

    async def compare_runs(self, run_id1: str, run_id2: str) -> Dict[str, Any]:
        """Compare two test runs to identify differences.

        Args:
            run_id1: First run ID to compare
            run_id2: Second run ID to compare

        Returns:
            Dictionary with comparison results
        """
        run1 = await self.get_run_details(run_id1)
        run2 = await self.get_run_details(run_id2)

        if not run1 or not run2:
            missing = []
            if not run1:
                missing.append(run_id1)
            if not run2:
                missing.append(run_id2)
            return {"success": False, "error": f"Run(s) not found: {', '.join(missing)}"}

        schema1 = run1["schema_name"]
        schema2 = run2["schema_name"]

        # Compare database tables across the two schemas
        async with async_session_maker() as session:
            # Get list of tables in schema1
            tables_result = await session.execute(
                text(
                    f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                AND table_name NOT IN (:metadata_table, :results_table)
            """
                ),
                {
                    "schema": schema1,
                    "metadata_table": self.metadata_table,
                    "results_table": self.results_table,
                },
            )

            tables = tables_result.scalars().all()

            differences = []
            for table_name in tables:
                # Compare row counts
                count_result = await session.execute(
                    text(
                        f"""
                    SELECT 
                        (SELECT COUNT(*) FROM "{schema1}"."{table_name}") AS count1,
                        (SELECT COUNT(*) FROM "{schema2}"."{table_name}") AS count2
                """
                    )
                )

                counts = count_result.mappings().one()

                if counts["count1"] != counts["count2"]:
                    differences.append(
                        {
                            "table": table_name,
                            "type": "row_count",
                            "run1_count": counts["count1"],
                            "run2_count": counts["count2"],
                            "difference": abs(counts["count1"] - counts["count2"]),
                        }
                    )
                    continue

                # If row counts match, check for content differences
                # This is just a simple check - you might want more sophisticated comparisons
                diff_count_result = await session.execute(
                    text(
                        f"""
                    SELECT COUNT(*) 
                    FROM (
                        SELECT * FROM "{schema1}"."{table_name}"
                        EXCEPT
                        SELECT * FROM "{schema2}"."{table_name}"
                    ) AS diff
                """
                    )
                )

                diff_count = diff_count_result.scalar_one()

                if diff_count > 0:
                    differences.append(
                        {
                            "table": table_name,
                            "type": "content",
                            "different_rows": diff_count,
                        }
                    )

        return {
            "success": True,
            "run1": {"id": run_id1, "schema": schema1, "status": run1["info"].get("status")},
            "run2": {"id": run_id2, "schema": schema2, "status": run2["info"].get("status")},
            "differences": differences,
            "identical": len(differences) == 0,
        }

    async def cleanup(self) -> None:
        """Reset the current run state without deleting the schema."""
        self.current_run_id = None
