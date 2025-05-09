"""add_missing_gathering_date_local

Revision ID: f5ff98afb66c
Revises: d23f57272fb4
Create Date: 2025-05-08 18:02:18.122162

"""

import sqlalchemy as sa
from sqlalchemy import inspect

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5ff98afb66c"
down_revision: Union[str, None] = "d23f57272fb4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Get database connection
    connection = op.get_bind()
    inspector = inspect(connection)

    # Check if the column already exists

    # Check if the column already exists
    columns = [column["name"] for column in inspector.get_columns("daily_chrome_summaries")]

    # Only add the column if it doesn't exist
    if "gathering_date_local" not in columns:
        op.add_column(
            "daily_chrome_summaries",
            sa.Column("gathering_date_local", sa.DateTime(timezone=False)),
        )
        print("Added gathering_date_local column to daily_chrome_summaries")
    else:
        print("Column gathering_date_local already exists in daily_chrome_summaries")


def downgrade() -> None:
    # Do nothing.
    # This migration is a double check to verify that something
    # from migration f249814dcabc went as planned.
    pass
