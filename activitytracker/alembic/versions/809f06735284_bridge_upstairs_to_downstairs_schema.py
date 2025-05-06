"""bridge_upstairs_to_downstairs_schema

Backfill migration to sync upstairs DB with downstairs schema

Revision ID: 809f06735284
Revises: 37bc06b24c3f
Create Date: 2025-04-21 20:05:40.733666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '809f06735284'
down_revision: Union[str, None] = '37bc06b24c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. SET transaction_timeout [intentionally skipped]

    # 2. Modify chrome_tabs.tab_title to have a limit of 120 characters
    # and change created_at from "with time zone" to "without time zone" and remove DEFAULT
    op.alter_column('chrome_tabs', 'tab_title',
                    existing_type=sa.VARCHAR(),
                    type_=sa.VARCHAR(120),
                    existing_nullable=True)

    # First remove the default constraint
    op.execute(
        "ALTER TABLE public.chrome_tabs ALTER COLUMN created_at DROP DEFAULT")

    # Then change the type
    op.alter_column('chrome_tabs', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(timezone=False),
                    existing_nullable=True)

    # 3. Modify client_timeline_entries columns: change text to character varying
    # Note: Since these are generated columns, we need to drop and recreate them

    # First, drop the generated columns
    op.execute('ALTER TABLE client_timeline_entries DROP COLUMN "clientFacingId"')
    op.execute('ALTER TABLE client_timeline_entries DROP COLUMN "content"')

    # Then add them back with the new type
    op.execute('''
    ALTER TABLE client_timeline_entries ADD COLUMN "clientFacingId" character varying 
    GENERATED ALWAYS AS (
        CASE
            WHEN ("group" = 'MOUSE'::public.charteventtype) THEN ('mouse-'::text || (id)::text)
            ELSE ('keyboard-'::text || (id)::text)
        END
    ) STORED
    ''')

    op.execute('''
    ALTER TABLE client_timeline_entries ADD COLUMN "content" character varying 
    GENERATED ALWAYS AS (
        CASE
            WHEN ("group" = 'MOUSE'::public.charteventtype) THEN ('Mouse Event '::text || (id)::text)
            ELSE ('Typing Session '::text || (id)::text)
        END
    ) STORED
    ''')

    # 4. Modify frames.created_at from "with time zone" to "without time zone"
    op.alter_column('frames', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(timezone=False),
                    existing_nullable=True)

    # 5. Remove the "day" column from precomputed_timelines
    op.drop_column('precomputed_timelines', 'day')

    # 6. Drop the program table and its related sequences/indexes
    op.drop_index('ix_program_window', table_name='program')
    op.drop_index('ix_program_id', table_name='program')
    op.drop_table('program')
    op.execute('DROP SEQUENCE IF EXISTS public.program_id_seq')

    # 7. Modify program_changes.created_at from "with time zone" to "without time zone"
    op.alter_column('program_changes', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(timezone=False),
                    existing_nullable=True)

    # 8. Modify video_files.created_at from "with time zone" to "without time zone"
    op.alter_column('video_files', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(timezone=False),
                    existing_nullable=True)


def downgrade():
    # Implement the reverse operations for a downgrade

    # 8. Change video_files.created_at back to "with time zone"
    op.alter_column('video_files', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=False),
                    type_=sa.TIMESTAMP(timezone=True),
                    existing_nullable=True)

    # 7. Change program_changes.created_at back to "with time zone"
    op.alter_column('program_changes', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=False),
                    type_=sa.TIMESTAMP(timezone=True),
                    existing_nullable=True)

    # 6. Recreate the program table and its related sequences/indexes
    op.execute('''
    CREATE SEQUENCE public.program_id_seq
        AS integer
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1
    ''')

    op.create_table('program',
                    sa.Column('id', sa.INTEGER(),
                              autoincrement=True, nullable=False),
                    sa.Column('window', sa.VARCHAR(),
                              autoincrement=False, nullable=True),
                    sa.Column('start_time', sa.TIMESTAMP(timezone=True),
                              autoincrement=False, nullable=True),
                    sa.Column('end_time', sa.TIMESTAMP(timezone=True),
                              autoincrement=False, nullable=True),
                    sa.Column('productive', sa.BOOLEAN(),
                              autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                              autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('id', name='program_pkey')
                    )

    op.create_index('ix_program_id', 'program', ['id'], unique=False)
    op.create_index('ix_program_window', 'program', ['window'], unique=False)
    op.execute(
        'ALTER TABLE ONLY public.program ALTER COLUMN id SET DEFAULT nextval(\'public.program_id_seq\'::regclass)')

    # 5. Add the "day" column back to precomputed_timelines
    op.add_column('precomputed_timelines',
                  sa.Column('day', sa.TIMESTAMP(timezone=True), nullable=True))

    # 4. Change frames.created_at back to "with time zone"
    op.alter_column('frames', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=False),
                    type_=sa.TIMESTAMP(timezone=True),
                    existing_nullable=True)

    # 3. Revert client_timeline_entries columns back to text type
    # Drop and recreate the generated columns
    op.execute('ALTER TABLE client_timeline_entries DROP COLUMN "clientFacingId"')
    op.execute('ALTER TABLE client_timeline_entries DROP COLUMN "content"')

    op.execute('''
    ALTER TABLE client_timeline_entries ADD COLUMN "clientFacingId" text 
    GENERATED ALWAYS AS (
        CASE
            WHEN ("group" = 'MOUSE'::public.charteventtype) THEN ('mouse-'::text || (id)::text)
            ELSE ('keyboard-'::text || (id)::text)
        END
    ) STORED
    ''')

    op.execute('''
    ALTER TABLE client_timeline_entries ADD COLUMN "content" text 
    GENERATED ALWAYS AS (
        CASE
            WHEN ("group" = 'MOUSE'::public.charteventtype) THEN ('Mouse Event '::text || (id)::text)
            ELSE ('Typing Session '::text || (id)::text)
        END
    ) STORED
    ''')

    # 2. Revert chrome_tabs.tab_title and created_at changes
    op.alter_column('chrome_tabs', 'tab_title',
                    existing_type=sa.VARCHAR(120),
                    type_=sa.VARCHAR(),
                    existing_nullable=True)

    # Change the timestamp type back
    op.alter_column('chrome_tabs', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=False),
                    type_=sa.TIMESTAMP(timezone=True),
                    existing_nullable=True)

    # Add back the default constraint
    op.execute(
        "ALTER TABLE public.chrome_tabs ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP")
