"""add _local fields to logs and summaries models

Revision ID: f249814dcabc
Revises: 16c7d3706d57
Create Date: 2025-04-30 14:31:30.385829

"""

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, text

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f249814dcabc"
down_revision: Union[str, None] = "16c7d3706d57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ⚠️ Set this to your local timezone before running!
TIMEZONE = "America/Los_Angeles"  # e.g., 'Asia/Tokyo'


def upgrade():
    if TIMEZONE is None:
        raise RuntimeError("Set the TIMEZONE variable in this migration before running it.")

    # Add columns
    op.add_column(
        "daily_program_summaries",
        sa.Column("gathering_date_local", sa.DateTime(timezone=False)),
    )
    op.add_column(
        "daily_chrome_summaries",
        sa.Column("gathering_date_local", sa.DateTime(timezone=False)),
    )

    op.add_column("program_logs", sa.Column("start_time_local", sa.DateTime(timezone=False)))
    op.add_column("program_logs", sa.Column("end_time_local", sa.DateTime(timezone=False)))
    op.add_column(
        "program_logs", sa.Column("gathering_date_local", sa.DateTime(timezone=False))
    )

    op.add_column("domain_logs", sa.Column("start_time_local", sa.DateTime(timezone=False)))
    op.add_column("domain_logs", sa.Column("end_time_local", sa.DateTime(timezone=False)))
    op.add_column(
        "domain_logs", sa.Column("gathering_date_local", sa.DateTime(timezone=False))
    )

    # Fill new _local fields from existing UTC fields
    for table_name, time_fields in [
        ("program_logs", ["start_time", "end_time", "gathering_date"]),
        ("domain_logs", ["start_time", "end_time", "gathering_date"]),
        ("daily_program_summaries", ["gathering_date"]),
        ("daily_chrome_summaries", ["gathering_date"]),
    ]:
        for field in time_fields:
            op.execute(
                text(
                    f"""
                    UPDATE {table_name}
                    SET {field}_local = ({field} AT TIME ZONE 'UTC') AT TIME ZONE :tz
                """
                ).bindparams(tz=TIMEZONE)
            )


def downgrade():
    # Remove gathering_date_local from DailySummaryBase derived tables
    op.drop_column("daily_program_summaries", "gathering_date_local")
    op.drop_column("daily_chrome_summaries", "gathering_date_local")

    # Remove local timezone fields from models inheriting from SummaryLogBase
    op.drop_column("program_logs", "start_time_local")
    op.drop_column("program_logs", "end_time_local")
    op.drop_column("program_logs", "gathering_date_local")

    op.drop_column("domain_logs", "start_time_local")
    op.drop_column("domain_logs", "end_time_local")
    op.drop_column("domain_logs", "gathering_date_local")
