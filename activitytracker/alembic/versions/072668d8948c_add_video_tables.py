"""add video tables

Revision ID: 072668d8948c
Revises: f5ff98afb66c
Create Date: 2025-05-22 13:37:05.682315

"""

import sqlalchemy as sa

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "072668d8948c"
down_revision: Union[str, None] = "f5ff98afb66c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create daily_video_summaries table
    op.create_table(
        "daily_video_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hours_spent", sa.Float(), nullable=False),
        sa.Column("gathering_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gathering_date_local", sa.DateTime(timezone=False), nullable=False),
        sa.Column("media_name", sa.String(), nullable=True),
        sa.Column("channel_name", sa.String(), nullable=True),
        sa.Column("platform", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_daily_video_summaries_id"), "daily_video_summaries", ["id"], unique=False
    )

    # Create video_logs table
    op.create_table(
        "video_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hours_spent", sa.Float(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_time_local", sa.DateTime(timezone=False), nullable=False),
        sa.Column("end_time_local", sa.DateTime(timezone=False), nullable=False),
        sa.Column("duration_in_sec", sa.Float(), nullable=True),
        sa.Column("gathering_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gathering_date_local", sa.DateTime(timezone=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("media_name", sa.String(), nullable=False),
        sa.Column("channel_name", sa.String(), nullable=True),
        sa.Column("platform", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_video_logs_id"), "video_logs", ["id"], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f("ix_video_logs_id"), table_name="video_logs")
    op.drop_index(op.f("ix_daily_video_summaries_id"), table_name="daily_video_summaries")

    # Drop tables
    op.drop_table("video_logs")
    op.drop_table("daily_video_summaries")
