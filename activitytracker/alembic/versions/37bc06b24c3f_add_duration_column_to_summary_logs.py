"""add_duration_column_to_summary_logs

Revision ID: 37bc06b24c3f
Revises: 2e33c084bdf4
Create Date: 2025-03-15 13:15:13.778889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37bc06b24c3f'
down_revision: Union[str, None] = '2e33c084bdf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add duration column to program_summary_logs table
    op.add_column('program_summary_logs',
                  sa.Column('duration', sa.Float(), nullable=True))

    # Add duration column to domain_summary_logs table
    op.add_column('domain_summary_logs',
                  sa.Column('duration', sa.Float(), nullable=True))


def downgrade():
    # Remove duration column from program_summary_logs table
    op.drop_column('program_summary_logs', 'duration')

    # Remove duration column from domain_summary_logs table
    op.drop_column('domain_summary_logs', 'duration')
