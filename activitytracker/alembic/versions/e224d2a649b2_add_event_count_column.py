"""add_event_count_column

Revision ID: e224d2a649b2
Revises: d486328ba19b
Create Date: 2025-02-17 13:12:15.848292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e224d2a649b2'
down_revision: Union[str, None] = 'd486328ba19b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the column, making it nullable since existing rows won't have a value
    op.add_column('precomputed_timelines', sa.Column(
        'eventCount', sa.Integer(), nullable=True))

    # Optionally, you can set a default value for existing rows
    # For example, if you want to set all existing rows to have eventCount = 0:
    op.execute(
        "UPDATE precomputed_timelines SET \"eventCount\" = 0 WHERE \"eventCount\" IS NULL")

    # If you want to make the column non-nullable after setting defaults:
    op.alter_column('precomputed_timelines', 'eventCount',
                    existing_type=sa.Integer(),
                    nullable=False)


def downgrade():
    op.drop_column('precomputed_timelines', 'eventCount')
