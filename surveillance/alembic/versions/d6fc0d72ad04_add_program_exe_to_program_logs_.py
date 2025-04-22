"""add program_exe to program logs & summaries

Revision ID: d6fc0d72ad04
Revises: 809f06735284
Create Date: 2025-04-21 21:39:44.940488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6fc0d72ad04'
down_revision: Union[str, None] = '809f06735284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('program_summary_logs',
                  sa.Column('exe_path', sa.String(length=255), nullable=True))
    op.add_column('daily_program_summaries',
                  sa.Column('exe_path', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('program_summary_logs', 'exe_path')
    op.drop_column('daily_program_summaries', 'exe_path')
