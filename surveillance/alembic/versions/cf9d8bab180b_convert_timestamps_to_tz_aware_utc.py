"""convert_timestamps_to_tz_aware_utc

Problem statement: Cols are all 'timestamp without timezone', but 
we need to store UTC timestamped datetimes. Further, all recorded data was from PST.

Solution statement: Go from timezone-naive, into PST, and transform from there into UTC.

Revision ID: cf9d8bab180b
Revises: 4f0875aef5cb
Create Date: 2025-02-23 15:38:29.545778

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = 'cf9d8bab180b'
down_revision = '4f0875aef5cb'  # previous revision id
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # First get all timestamp columns
    result = conn.execute(text("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE data_type = 'timestamp without time zone' 
            AND table_schema = 'public';
    """))
    columns = list(result)  # Store results since we'll need them twice

    # Step 1: Convert naive timestamps to timezone-aware PST
    for table_name, column_name in columns:
        op.execute(text(f"""
            ALTER TABLE "{table_name}" 
            ALTER COLUMN "{column_name}" 
            TYPE TIMESTAMP WITH TIME ZONE 
            USING "{column_name}" AT TIME ZONE 'America/Los_Angeles';
        """))

    # Step 2: Convert PST timestamps to UTC
    for table_name, column_name in columns:
        op.execute(text(f"""
            UPDATE "{table_name}"
            SET "{column_name}" = "{column_name}" AT TIME ZONE 'UTC';
        """))


def downgrade():
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE data_type = 'timestamp with time zone' 
            AND table_schema = 'public';
    """))

    for table_name, column_name in result:
        # Convert back to naive timestamps in local time
        op.execute(text(f"""
            ALTER TABLE {table_name} 
            ALTER COLUMN {column_name} 
            TYPE TIMESTAMP WITHOUT TIME ZONE 
            USING {column_name} AT TIME ZONE 'America/Los_Angeles';
        """))
