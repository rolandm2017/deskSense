"""mk_eventcount_nullable

Revision ID: 4f0875aef5cb
Revises: remove_computed_columns
Create Date: 2025-02-19 13:58:45.922496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f0875aef5cb'
down_revision: Union[str, None] = 'remove_computed_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('precomputed_timelines', 'eventCount',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade():
    op.alter_column('precomputed_timelines', 'eventCount',
                    existing_type=sa.Integer(),
                    nullable=False)
