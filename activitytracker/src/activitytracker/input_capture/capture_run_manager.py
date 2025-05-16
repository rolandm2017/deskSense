# capture_run_manager.py
import json
import os
import uuid

from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import text

import time
from datetime import datetime, timedelta

from typing import Any, Dict, List, Optional

from activitytracker.config.definitions import program_environment
from activitytracker.db.database import (
    Base,
    simulation_regular_session_maker,
    simulation_sync_engine,
)
from activitytracker.util.console_logger import ConsoleLogger


def get_timestamp_string():
    """Returns current time as YYYY-MM-DD_HH-MM-SS string for file naming."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

    # TODO: I need to show that i got the inputs and the outputs


# TODO: IMPORTANT: Just get the session id from the server to the ext.


class CaptureRunManager:
    """Manages test runs and their execution within isolated database schemas."""

    def __init__(self, schema_manager=None):
        """Initialize the test run manager.

        Args:
            schema_manager: Optional schema manager instance to use. If None,
                            a reference to the global test_schema_manager will be used.
        """
        # Import here to avoid circular imports
        from .test_schema_manager import set_sync_search_path, test_schema_manager

        self.set_sync_search_path = set_sync_search_path
        self.run_id = self.generate_run_id()
        self.session_active = program_environment.data_capture_session

        # Import here to avoid circular imports
        if not schema_manager:
            from activitytracker.input_capture.test_schema_manager import (
                test_schema_manager,
            )

            self.schema_manager = test_schema_manager
        else:
            self.schema_manager = schema_manager
        self.duration_in_minutes = 1
        self.test_end_time = None
        self.current_run_id: Optional[str] = None
        self.metadata_table = "test_run_metadata"
        self.results_table = "test_run_results"
        self.filename = self.make_filename()
        self.logger = ConsoleLogger()

    # TODO: a conclude() called in if_test_is_over

    def make_filename(self):
        logs_dir = os.path.join(".", "logs")

        os.makedirs(logs_dir, exist_ok=True)

        return os.path.join(logs_dir, "input_from_" + get_timestamp_string() + ".json")

    def generate_run_id(self) -> str:
        """Generate a unique ID for a test run."""
        timestamp = int(time.time())
        random_suffix = uuid.uuid4().hex[:6]
        return f"run_{timestamp}_{random_suffix}"

    def check_if_test_is_over(self):
        now = datetime.now()
        print(self.test_end_time, "80ru")
        if self.test_end_time:
            print(now, "82ru")
            if now > self.test_end_time:
                # Close session
                self.conclude_capture_session()

    def conclude_capture_session(self):
        program_environment.data_capture_session = False  # Will reset on server restart
        # Freeze the schema so no more modifications
        self.freeze("PASSED")

    def initialize(
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
        schema_name = self.schema_manager.generate_schema_name()
        print("schema name:", schema_name)
        # import activitytracker.db.models lives here for a reason: registering with Base
        import activitytracker.db.models  # package where your models live

        conn = simulation_sync_engine.connect().execution_options(
            schema_translate_map={None: schema_name}
        )

        self.schema_manager.create_schema_with_conn(
            schema_name, conn, test_name=test_name, input_file=input_capture_file
        )
        # schema_name = self.schema_manager.create_schema(
        #     schema_name, test_name=test_name, input_file=input_capture_file
        # )

        # Generate run ID
        run_id = self.generate_run_id()
        self.current_run_id = run_id
        run_start_as_float = time.time()
        self.run_start_time = datetime.fromtimestamp(run_start_as_float)

        test_end_time = self.run_start_time + timedelta(minutes=self.duration_in_minutes)
        print("Setting test end time", test_end_time)
        self.test_end_time = test_end_time
        self.logger.log_yellow(
            f"Test will end at: " + self.test_end_time.strftime("%H:%M:%S")
        )

        json_dump_of_test_info = json.dumps(
            {
                "name": test_name,
                "input_file": input_capture_file,
                "created_at": str(time.time()),
                "status": "CREATED",
            }
        )

        # Create test run tables in the schema
        self.create_test_run_tables(schema_name, json_dump_of_test_info)

        self.create_all_model_tables(schema_name)

        # Make sure all your models are imported and registered with Base
        # Import your models here if they're not already imported

        # Now create all tables with the schema explicitly specified
        # Create all the usual (development) tables in the schema
        self.logger.log_white("Creating all tables for schema " + schema_name)
        self.logger.log_white("Creating all tables")
        self.logger.log_white("Creating all tables")

        # The key fix: Use a schema-specific MetaData instance for table creation
        metadata = MetaData(schema=schema_name)
        for table in Base.metadata.tables.values():
            # Create a copy of the table with the new schema
            table.schema = schema_name
            # This effectively clones each table definition but with the new schema

        # Base.metadata.create_all(bind=conn)

        print("Models registered with Base:", Base.metadata.tables.keys())

        # TODO: Insert the string enums also
        # TODO: Insert the string enums also
        # TODO: Insert the string enums also

        # for table in Base.metadata.tables.values():
        #     print(f"{table.fullname} -> schema: {table.schema}")
        # for table in Base.metadata.sorted_tables:
        #     print(f"Table: {table.name}, schema: {table.schema}")

        # Only for debugging: Update the schema in metadata to maintain consistency
        for table in Base.metadata.tables.values():
            table.schema = schema_name
            print(f"{table.fullname} -> schema: {table.schema}")

        # Set the current schema for future operations
        self.schema_manager.set_schema(schema_name)

        # Verify tables were created
        self.verify_tables(schema_name)

        return run_id

    def create_test_run_tables(self, schema_name, test_info_json_dump):
        # Create test run tables in the schema
        with simulation_regular_session_maker() as session:
            # Set search path for this session
            session.execute(text(f'SET search_path TO "{schema_name}", public'))

            # Create results table directly using SQL (more reliable)
            session.execute(
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
            session.execute(
                text(
                    f"""
                INSERT INTO "{schema_name}".{self.metadata_table} (key, value)
                VALUES ('run_info', :run_info)
                """
                ),
                {"run_info": test_info_json_dump},
            )

            session.commit()

    def create_all_model_tables(self, schema_name):
        # The important part: Explicitly create all model tables in the schema
        with simulation_sync_engine.connect() as conn:
            # Set search path for this connection
            conn.execute(text(f'SET search_path TO "{schema_name}", public'))

            # Create ENUM types first
            conn.execute(
                text(
                    f"""
                CREATE TYPE "{schema_name}"."systemstatustype" AS ENUM ('program_started', 'online', 'shutdown', 'test_startup');
            """
                )
            )

            conn.execute(
                text(
                    f"""
                CREATE TYPE "{schema_name}"."charteventtype" AS ENUM ('MOUSE', 'KEYBOARD');
            """
                )
            )

            # Create model tables one by one with explicit schema
            for table_name in [
                "daily_program_summaries",
                "daily_chrome_summaries",
                "program_logs",
                "domain_logs",
                "typing_sessions",
                "mouse_moves",
                "client_timeline_entries",
                "precomputed_timelines",
                "system_status",
            ]:
                # Get the table definition from Base.metadata
                table = Base.metadata.tables[table_name]

                # Explicitly set the schema for this table
                table.schema = schema_name

                # Create the table DDL
                create_stmt = str(
                    CreateTable(table).compile(
                        dialect=conn.dialect,
                    )
                )

                # Execute the create statement
                self.logger.log_white(f"Creating table {schema_name}.{table_name}")
                conn.execute(text(create_stmt))

            conn.commit()

            # Log completion
            self.logger.log_white(
                f"Successfully created all tables in schema: {schema_name}"
            )

    def record_event(
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

        with simulation_regular_session_maker() as session:
            # Set search path
            self.set_sync_search_path(session)

            # Insert the event
            result = session.execute(
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
            session.commit()

            return event_id

    def freeze(self, status: str, notes: str | None = None) -> bool:
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
        schema_updated = self.schema_manager.mark_schema_status(status, notes)

        with simulation_regular_session_maker() as session:
            # Set search path
            self.set_sync_search_path(session)

            # Update run metadata
            try:
                session.execute(
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
                        "duration": f'"{time.time() - float(self._get_start_time())}"',
                    },
                )

                if notes:
                    session.execute(
                        text(
                            f"""
                        UPDATE {self.metadata_table}
                        SET value = jsonb_set(value, '{{notes}}', :notes::jsonb)
                        WHERE key = 'run_info'
                    """
                        ),
                        {"notes": f'"{notes}"'},
                    )

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error freezing test run: {e}")
                return False

    def _get_start_time(self) -> str:
        """Helper to retrieve the start time of the current run."""
        with simulation_regular_session_maker() as session:
            # Set search path
            self.set_sync_search_path(session)

            result = session.execute(
                text(
                    f"""
                SELECT value->>'started_at' FROM {self.metadata_table}
                WHERE key = 'run_info'
            """
                )
            )

            start_time = result.scalar_one_or_none() or "0"
            return start_time

    def get_run_details(self, run_id: str | None = None) -> Optional[Dict[str, Any]]:
        """Get details about a specific test run.

        Args:
            run_id: The run ID to fetch details for, or current run if None

        Returns:
            Dictionary with run details or None if not found
        """
        run_id = run_id or self.current_run_id
        if not run_id:
            return None

        with simulation_regular_session_maker() as session:
            # Find the schema containing this run
            schemas = self.schema_manager.list_test_schemas()

            for schema in schemas:
                schema_name = schema["schema_name"]

                # Check if this schema contains our run
                try:
                    result = session.execute(
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
                        events_result = session.execute(
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

    def list_runs(self) -> List[Dict[str, Any]]:
        """List all test runs across all schemas.

        Returns:
            List of dictionaries with run information
        """
        runs = []
        schemas = self.schema_manager.list_test_schemas()

        with simulation_regular_session_maker() as session:
            for schema in schemas:
                schema_name = schema["schema_name"]

                try:
                    result = session.execute(
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

    def compare_runs(self, run_id1: str, run_id2: str) -> Dict[str, Any]:
        """Compare two test runs to identify differences.

        Args:
            run_id1: First run ID to compare
            run_id2: Second run ID to compare

        Returns:
            Dictionary with comparison results
        """
        run1 = self.get_run_details(run_id1)
        run2 = self.get_run_details(run_id2)

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
        with simulation_regular_session_maker() as session:
            # Get list of tables in schema1
            tables_result = session.execute(
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
                count_result = session.execute(
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
                diff_count_result = session.execute(
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

    def verify_tables(self, schema_name):
        """Verify that tables were actually created in the database."""
        with simulation_sync_engine.connect() as conn:
            # Check if key tables exist
            for table_name in ["system_status", "program_logs", "daily_program_summaries"]:
                result = conn.execute(
                    text(
                        f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
                    )
                    """
                    )
                )
                exists = result.scalar()
                self.logger.log_white(f"Table {schema_name}.{table_name} exists: {exists}")

                if not exists:
                    self.logger.log_yellow(
                        f"WARNING: Table {schema_name}.{table_name} was not created!"
                    )

                    # Try to create it again
                    self.logger.log_yellow(f"Attempting to recreate {table_name}...")
                    try:
                        if table_name == "system_status":
                            conn.execute(
                                text(
                                    f"""
                                CREATE TABLE IF NOT EXISTS "{schema_name}".system_status (
                                    id SERIAL PRIMARY KEY,
                                    status TEXT NOT NULL,
                                    created_at TIMESTAMPTZ NOT NULL
                                )
                                """
                                )
                            )
                        elif table_name == "program_logs":
                            conn.execute(
                                text(
                                    f"""
                                CREATE TABLE IF NOT EXISTS "{schema_name}".program_logs (
                                    id SERIAL PRIMARY KEY,
                                    hours_spent FLOAT NOT NULL,
                                    start_time TIMESTAMPTZ NOT NULL,
                                    end_time TIMESTAMPTZ NOT NULL,
                                    start_time_local TIMESTAMP NOT NULL,
                                    end_time_local TIMESTAMP NOT NULL,
                                    duration_in_sec FLOAT,
                                    gathering_date TIMESTAMPTZ NOT NULL,
                                    gathering_date_local TIMESTAMP NOT NULL,
                                    created_at TIMESTAMPTZ,
                                    exe_path_as_id TEXT NOT NULL,
                                    process_name TEXT NOT NULL,
                                    program_name TEXT NOT NULL
                                )
                                """
                                )
                            )
                        elif table_name == "daily_program_summaries":
                            conn.execute(
                                text(
                                    f"""
                                CREATE TABLE IF NOT EXISTS "{schema_name}".daily_program_summaries (
                                    id SERIAL PRIMARY KEY,
                                    hours_spent FLOAT NOT NULL,
                                    gathering_date TIMESTAMPTZ NOT NULL,
                                    gathering_date_local TIMESTAMP NOT NULL,
                                    exe_path_as_id TEXT NOT NULL,
                                    process_name TEXT NOT NULL,
                                    program_name TEXT NOT NULL
                                )
                                """
                                )
                            )

                        conn.commit()
                        self.logger.log_white(
                            f"Successfully recreated {schema_name}.{table_name}"
                        )
                    except Exception as e:
                        self.logger.log_yellow(f"Failed to recreate {table_name}: {e}")

            # Extra verification - try to actually insert and query data
            try:
                # Insert a test record
                conn.execute(
                    text(
                        f"""
                    INSERT INTO "{schema_name}".system_status (status, created_at) 
                    VALUES ('test_startup', NOW())
                    """
                    )
                )
                conn.commit()

                # Try to query it
                result = conn.execute(
                    text(
                        f"""
                    SELECT COUNT(*) FROM "{schema_name}".system_status
                    """
                    )
                )
                count = result.scalar()
                self.logger.log_white(
                    f"Inserted and verified system_status table works: {count} records"
                )
            except Exception as e:
                self.logger.log_yellow(f"Verification insert/query failed: {e}")

                # Last resort: run VACUUM ANALYZE to update planner statistics
                try:
                    conn.execute(text(f'VACUUM ANALYZE "{schema_name}"."system_status"'))
                    self.logger.log_white("Ran VACUUM ANALYZE on system_status table")
                except Exception as vacuum_error:
                    self.logger.log_yellow(f"VACUUM ANALYZE failed: {vacuum_error}")

    def create_tables_with_direct_sql(self, schema_name):
        # Create tables using direct SQL - guaranteed to work
        with simulation_sync_engine.connect() as conn:
            # Use AUTOCOMMIT for DDL
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")

            # Create the system_status table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".system_status (
                id SERIAL PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
                )
            )

            # Create daily_program_summaries table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".daily_program_summaries (
                id SERIAL PRIMARY KEY,
                hours_spent FLOAT NOT NULL,
                gathering_date TIMESTAMPTZ NOT NULL,
                gathering_date_local TIMESTAMP NOT NULL,
                exe_path_as_id TEXT NOT NULL,
                process_name TEXT NOT NULL,
                program_name TEXT NOT NULL
            )
            """
                )
            )

            # Create daily_chrome_summaries table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".daily_chrome_summaries (
                id SERIAL PRIMARY KEY,
                hours_spent FLOAT NOT NULL,
                gathering_date TIMESTAMPTZ NOT NULL,
                gathering_date_local TIMESTAMP NOT NULL,
                domain_name TEXT NOT NULL
            )
            """
                )
            )

            # Create program_logs table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".program_logs (
                id SERIAL PRIMARY KEY,
                hours_spent FLOAT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                start_time_local TIMESTAMP NOT NULL,
                end_time_local TIMESTAMP NOT NULL,
                duration_in_sec FLOAT,
                gathering_date TIMESTAMPTZ NOT NULL,
                gathering_date_local TIMESTAMP NOT NULL,
                created_at TIMESTAMPTZ,
                exe_path_as_id TEXT NOT NULL,
                process_name TEXT NOT NULL,
                program_name TEXT NOT NULL
            )
            """
                )
            )

            # Create domain_logs table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".domain_logs (
                id SERIAL PRIMARY KEY,
                hours_spent FLOAT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                start_time_local TIMESTAMP NOT NULL,
                end_time_local TIMESTAMP NOT NULL,
                duration_in_sec FLOAT,
                gathering_date TIMESTAMPTZ NOT NULL,
                gathering_date_local TIMESTAMP NOT NULL,
                created_at TIMESTAMPTZ,
                domain_name TEXT NOT NULL
            )
            """
                )
            )

            # Create typing_sessions table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".typing_sessions (
                id SERIAL PRIMARY KEY,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL
            )
            """
                )
            )

            # Create mouse_moves table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".mouse_moves (
                id SERIAL PRIMARY KEY,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL
            )
            """
                )
            )

            # Create client_timeline_entries table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".client_timeline_entries (
                id SERIAL PRIMARY KEY,
                "clientFacingId" TEXT GENERATED ALWAYS AS 
                    (CASE WHEN "group" = 'MOUSE' THEN 'mouse-' || id ELSE 'keyboard-' || id END) STORED,
                "group" TEXT NOT NULL,
                content TEXT GENERATED ALWAYS AS 
                    (CASE WHEN "group" = 'MOUSE' THEN 'Mouse Event ' || id ELSE 'Typing Session ' || id END) STORED,
                start TIMESTAMPTZ NOT NULL,
                "end" TIMESTAMPTZ NOT NULL
            )
            """
                )
            )

            # Create precomputed_timelines table
            conn.execute(
                text(
                    f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".precomputed_timelines (
                id SERIAL PRIMARY KEY,
                "clientFacingId" TEXT NOT NULL,
                "group" TEXT NOT NULL,
                content TEXT NOT NULL,
                start TIMESTAMPTZ NOT NULL,
                "end" TIMESTAMPTZ NOT NULL,
                "eventCount" INTEGER NOT NULL
            )
            """
                )
            )

            self.logger.log_white(f"All tables successfully created in schema {schema_name}")
