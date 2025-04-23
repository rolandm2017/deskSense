"""rename_exe_path_and_add_process_name

Revision ID: d72c5c22368c
Revises: d6fc0d72ad04
Create Date: 2025-04-22 13:37:11.697155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd72c5c22368c'
down_revision: Union[str, None] = 'd6fc0d72ad04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename exe_path to exe_path_as_id in both tables
    op.alter_column('program_summary_logs', 'exe_path',
                    new_column_name='exe_path_as_id')
    op.alter_column('daily_program_summaries', 'exe_path',
                    new_column_name='exe_path_as_id')

    # Add process_name column to program_summary_logs
    op.add_column('program_summary_logs',
                  sa.Column('process_name', sa.String(length=255), nullable=True))


def downgrade():
    # Remove added column
    op.drop_column('program_summary_logs', 'process_name')

    # Rename exe_path_as_id back to exe_path in both tables
    op.alter_column('program_summary_logs', 'exe_path_as_id',
                    new_column_name='exe_path')
    op.alter_column('daily_program_summaries',
                    'exe_path_as_id', new_column_name='exe_path')
