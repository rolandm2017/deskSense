"""Set max length for window, detail, url

Revision ID: 085f4f1c53a5
Revises: cf9d8bab180b
Create Date: 2025-02-24 14:34:44.541973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision: str = '085f4f1c53a5'
down_revision: Union[str, None] = 'cf9d8bab180b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Truncate values before altering the column type
    conn.execute(sa.text(
        'UPDATE program_changes SET "window" = LEFT("window", 120), "detail" = LEFT("detail", 120)'))
    conn.execute(sa.text('UPDATE chrome_tabs SET "url" = LEFT("url", 120)'))

    with op.batch_alter_table('program_changes') as batch_op:
        batch_op.alter_column('window', type_=sa.String(120))
        batch_op.alter_column('detail', type_=sa.String(120))

    with op.batch_alter_table('chrome_tabs') as batch_op:
        batch_op.alter_column('url', type_=sa.String(120))


def downgrade():
    with op.batch_alter_table('program_changes') as batch_op:
        batch_op.alter_column('window', type_=sa.String())  # Removes limit
        # Revert to previous limit
        batch_op.alter_column('detail', type_=sa.String(255))

    with op.batch_alter_table('chrome_tabs') as batch_op:
        batch_op.alter_column('url', type_=sa.String())  # Removes limit
