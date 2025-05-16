"""update sys status table; drop frames, video_files

Revision ID: d23f57272fb4
Revises: f249814dcabc
Create Date: 2025-05-06 19:22:52.182187

"""
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import text

from typing import Sequence, Union

from alembic import op

# Define the enum type - needed in the migration


# NOTE that the enums were created by hand, without Sqlalchemy translating this into an enum
class SystemStatusType(Enum):
    PROGRAM_STARTED = "program_started"
    ONLINE = "online"
    SHUTDOWN = "shutdown"


# revision identifiers, used by Alembic.
revision: str = 'd23f57272fb4'
down_revision: Union[str, None] = 'f249814dcabc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    enum_name = "systemstatustype"
    # NOTE that the enums were created by hand, without Sqlalchemy translating the class into an enum

    enum_values = ["program_started", "online", "shutdown"]

    # Drop old tables if they exist
    for old_table in ['frames', 'video_files']:
        exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables WHERE table_name = '{old_table}'
            )
        """)).scalar()
        if exists:
            op.drop_table(old_table)

    # 1. Create a new enum type with the desired values
    op.execute(text("""
        CREATE TYPE systemstatustype_new AS ENUM (
            'program_started',
            'online',
            'shutdown'
        );
    """))

    op.execute(sa.text("DELETE FROM system_change_log"))

    # 2. Alter the 'status' column on 'system_status' to use the new enum
    op.execute(text("""
        ALTER TABLE system_change_log
        ALTER COLUMN status TYPE systemstatustype_new
        USING status::text::systemstatustype_new;
    """))

    # 3. Drop the old enum type
    op.execute(text("DROP TYPE systemstatustype;"))

    # 4. Rename the new enum type to the old name
    op.execute(text("""
        ALTER TYPE systemstatustype_new RENAME TO systemstatustype;
    """))

    op.rename_table('system_change_log', 'system_status')


def downgrade():
    # Simple downgrade - drop the table
    op.drop_table('system_status')

    # Drop the enum type
    op.execute(text("DROP TYPE IF EXISTS systemstatustype"))

    # Drop any straggler status-related enums
    conn = op.get_bind()
    old_enums = conn.execute(text("""
        SELECT typname FROM pg_type
        WHERE typname LIKE '%status%' AND typcategory = 'E'
    """)).fetchall()

    for (enum_name,) in old_enums:
        op.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))
