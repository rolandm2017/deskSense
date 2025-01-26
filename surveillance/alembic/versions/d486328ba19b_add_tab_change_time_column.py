"""add_tab_change_time_column

Revision ID: d486328ba19b
Revises: 2bb793da14eb
Create Date: 2025-01-26 09:02:36.264880

"""
from alembic import op
import sqlalchemy as sa

# These variables are required
revision = 'd486328ba19b'
down_revision = "2bb793da14eb"  # the ID of your previous migration
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chrome_tabs', sa.Column(
        'tab_change_time', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('chrome_tabs', 'tab_change_time')
