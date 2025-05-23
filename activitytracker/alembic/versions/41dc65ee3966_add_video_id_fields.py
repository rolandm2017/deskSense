"""add video id fields

Revision ID: 41dc65ee3966
Revises: 072668d8948c
Create Date: 2025-05-22 17:04:32.815286

"""

import sqlalchemy as sa

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "41dc65ee3966"
down_revision: Union[str, None] = "072668d8948c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# New migration file
def upgrade() -> None:
    op.add_column("daily_video_summaries", sa.Column("video_id", sa.String(), nullable=True))
    op.add_column("video_logs", sa.Column("video_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("video_logs", "video_id")
    op.drop_column("daily_video_summaries", "video_id")
