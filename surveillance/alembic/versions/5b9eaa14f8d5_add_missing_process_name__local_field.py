"""add missing process_name, _local field

Revision ID: 5b9eaa14f8d5
Revises: f249814dcabc
Create Date: 2025-05-05 11:04:16.519350

Exists because my actual schema didn't match what Alembic thought it was.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b9eaa14f8d5'
down_revision: Union[str, None] = 'f249814dcabc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check and add process_name
    if 'process_name' not in [col['name'] for col in inspector.get_columns('daily_program_summaries')]:
        op.add_column('daily_program_summaries',
                      sa.Column('process_name', sa.String(255), nullable=True))

    # Check and add gathering_date_local
    if 'gathering_date_local' not in [col['name'] for col in inspector.get_columns('daily_program_summaries')]:
        op.add_column('daily_program_summaries',
                      sa.Column('gathering_date_local', sa.DateTime(timezone=False), nullable=True))


def downgrade() -> None:
    pass
