"""remove_computed_columns

Remove computed columns from precomputed_timelines table

Revision ID: a4081ff07d47
Revises: 58f401419c53
Create Date: 2025-02-19 13:54:46.221672

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision = 'remove_computed_columns'
down_revision = '58f401419c53'
branch_labels = None
depends_on = None


def upgrade():
    # First, drop the existing computed columns
    op.drop_column('precomputed_timelines', 'clientFacingId')
    op.drop_column('precomputed_timelines', 'content')

    # Then add them back as regular string columns
    op.add_column('precomputed_timelines',
                  sa.Column('clientFacingId', sa.String(), nullable=True)
                  )
    op.add_column('precomputed_timelines',
                  sa.Column('content', sa.String(), nullable=True)
                  )


def downgrade():
    # Drop the regular string columns
    op.drop_column('precomputed_timelines', 'clientFacingId')
    op.drop_column('precomputed_timelines', 'content')

    # Add back the computed columns
    op.add_column('precomputed_timelines',
                  sa.Column('clientFacingId', sa.String(),
                            sa.Computed(
                      "CASE WHEN \"group\" = 'MOUSE' THEN 'mouse-' || id::TEXT ELSE 'keyboard-' || id::TEXT END",
                      persisted=True
                  ),
                      nullable=True
                  )
                  )
    op.add_column('precomputed_timelines',
                  sa.Column('content', sa.String(),
                            sa.Computed(
                      "CASE WHEN \"group\" = 'MOUSE' THEN 'Mouse Event ' || id::TEXT ELSE 'Typing Session ' || id::TEXT END",
                      persisted=True
                  ),
                      nullable=True
                  )
                  )
