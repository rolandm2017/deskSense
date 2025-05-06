"""add_event_count_column

Revision ID: 58f401419c53
Revises: e224d2a649b2
Create Date: 2025-02-17 13:19:09.489492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58f401419c53'
down_revision: Union[str, None] = 'e224d2a649b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
