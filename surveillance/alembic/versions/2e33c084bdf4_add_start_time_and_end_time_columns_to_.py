"""Add start_time and end_time columns to SummaryLog models

Revision ID: 2e33c084bdf4
Revises: 085f4f1c53a5
Create Date: 2025-03-10 12:49:02.414336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e33c084bdf4'
down_revision: Union[str, None] = '085f4f1c53a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add start_time and end_time columns to program_summary_logs table
    op.add_column('program_summary_logs', sa.Column(
        'start_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('program_summary_logs', sa.Column(
        'end_time', sa.DateTime(timezone=True), nullable=True))

    # Add start_time and end_time columns to domain_summary_logs table
    op.add_column('domain_summary_logs', sa.Column(
        'start_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('domain_summary_logs', sa.Column(
        'end_time', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove start_time and end_time columns from program_summary_logs table
    op.drop_column('program_summary_logs', 'end_time')
    op.drop_column('program_summary_logs', 'start_time')

    # Remove start_time and end_time columns from domain_summary_logs table
    op.drop_column('domain_summary_logs', 'end_time')
    op.drop_column('domain_summary_logs', 'start_time')
