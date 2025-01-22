"""add_computed_columns

Revision ID: 2bb793da14eb
Revises: 
Create Date: 2025-01-22 10:01:52.581332

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bb793da14eb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop existing columns
    op.execute(text('ALTER TABLE client_timeline_entries DROP COLUMN content;'))
    op.execute(
        text('ALTER TABLE client_timeline_entries DROP COLUMN "clientFacingId";'))

    # Add computed columns
    op.execute(text('''
        ALTER TABLE client_timeline_entries 
        ADD COLUMN content TEXT GENERATED ALWAYS AS 
        (CASE WHEN "group" = 'MOUSE' THEN 'Mouse Event ' || id::text 
         ELSE 'Typing Session ' || id::text END) STORED;
    '''))

    op.execute(text('''
        ALTER TABLE client_timeline_entries 
        ADD COLUMN "clientFacingId" TEXT GENERATED ALWAYS AS 
        (CASE WHEN "group" = 'MOUSE' THEN 'mouse-' || id::text 
         ELSE 'keyboard-' || id::text END) STORED;
    '''))


def downgrade():
    op.drop_column('client_timeline_entries', 'clientFacingId')
    op.drop_column('client_timeline_entries', 'content')
