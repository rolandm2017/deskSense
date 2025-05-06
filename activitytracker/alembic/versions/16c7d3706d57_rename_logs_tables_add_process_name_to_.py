"""Rename logs tables; add process_name to ProgramSummary

Revision ID: 16c7d3706d57
Revises: d72c5c22368c
Create Date: 2025-04-29 15:19:07.141406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '16c7d3706d57'
down_revision: Union[str, None] = 'd72c5c22368c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # 1. Add process_name to daily_program_summaries
    op.add_column('daily_program_summaries', 
                  sa.Column('process_name', sa.String(255), nullable=True))
    
    # 2. Handle the duration field - convert from hours to seconds (multiply by 3600)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # For program_summary_logs
    if 'duration' in [col['name'] for col in inspector.get_columns('program_summary_logs')]:
        # First add the new column
        op.add_column('program_summary_logs', 
                      sa.Column('duration_in_sec', sa.Float(), nullable=True))
        
        # Convert values from hours to seconds (multiply by 3600)
        op.execute(text(
            "UPDATE program_summary_logs SET duration_in_sec = duration * 3600 WHERE duration IS NOT NULL"
        ))
        
        # Drop the old column
        op.drop_column('program_summary_logs', 'duration')
    else:
        # Column doesn't exist, just add the new one
        op.add_column('program_summary_logs', 
                      sa.Column('duration_in_sec', sa.Float(), nullable=True))
    
    # For domain_summary_logs
    if 'duration' in [col['name'] for col in inspector.get_columns('domain_summary_logs')]:
        # First add the new column
        op.add_column('domain_summary_logs', 
                      sa.Column('duration_in_sec', sa.Float(), nullable=True))
        
        # Convert values from hours to seconds (multiply by 3600)
        op.execute(text(
            "UPDATE domain_summary_logs SET duration_in_sec = duration * 3600 WHERE duration IS NOT NULL"
        ))
        
        # Drop the old column
        op.drop_column('domain_summary_logs', 'duration')
    else:
        # Column doesn't exist, just add the new one
        op.add_column('domain_summary_logs', 
                      sa.Column('duration_in_sec', sa.Float(), nullable=True))
    
    # 3. Rename tables
    op.rename_table('program_summary_logs', 'program_logs')
    op.rename_table('domain_summary_logs', 'domain_logs')


def downgrade():
    # Reverse all operations from upgrade
    
    # 3. Restore original table names
    op.rename_table('program_logs', 'program_summary_logs')
    op.rename_table('domain_logs', 'domain_summary_logs')
    
    # 2. Convert from seconds back to hours (divide by 3600)
    # Add back 'duration' column
    op.add_column('program_summary_logs', sa.Column('duration', sa.Float(), nullable=True))
    op.add_column('domain_summary_logs', sa.Column('duration', sa.Float(), nullable=True))
    
    # Convert values
    op.execute(text(
        "UPDATE program_summary_logs SET duration = duration_in_sec / 3600 WHERE duration_in_sec IS NOT NULL"
    ))
    op.execute(text(
        "UPDATE domain_summary_logs SET duration = duration_in_sec / 3600 WHERE duration_in_sec IS NOT NULL"
    ))
    
    # Drop the seconds columns
    op.drop_column('program_summary_logs', 'duration_in_sec')
    op.drop_column('domain_summary_logs', 'duration_in_sec')
    
    # 1. Remove process_name from daily_program_summaries
    op.drop_column('daily_program_summaries', 'process_name')