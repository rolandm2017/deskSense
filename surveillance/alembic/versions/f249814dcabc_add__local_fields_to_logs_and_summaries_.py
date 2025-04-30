"""add _local fields to logs and summaries models

Revision ID: f249814dcabc
Revises: 16c7d3706d57
Create Date: 2025-04-30 14:31:30.385829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, DateTime


# revision identifiers, used by Alembic.
revision: str = 'f249814dcabc'
down_revision: Union[str, None] = '16c7d3706d57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add gathering_date_local to DailySummaryBase derived tables
    op.add_column('daily_program_summaries', Column('gathering_date_local', DateTime(timezone=False)))
    op.add_column('daily_chrome_summaries', Column('gathering_date_local', DateTime(timezone=False)))
    
    # Add local timezone fields to models inheriting from SummaryLogBase
    op.add_column('program_logs', Column('start_time_local', DateTime(timezone=False)))
    op.add_column('program_logs', Column('end_time_local', DateTime(timezone=False)))
    op.add_column('program_logs', Column('gathering_date_local', DateTime(timezone=False)))
    
    op.add_column('domain_logs', Column('start_time_local', DateTime(timezone=False)))
    op.add_column('domain_logs', Column('end_time_local', DateTime(timezone=False)))
    op.add_column('domain_logs', Column('gathering_date_local', DateTime(timezone=False)))


def downgrade():
    # Remove gathering_date_local from DailySummaryBase derived tables
    op.drop_column('daily_program_summaries', 'gathering_date_local')
    op.drop_column('daily_chrome_summaries', 'gathering_date_local')
    
    # Remove local timezone fields from models inheriting from SummaryLogBase
    op.drop_column('program_logs', 'start_time_local')
    op.drop_column('program_logs', 'end_time_local')
    op.drop_column('program_logs', 'gathering_date_local')
    
    op.drop_column('domain_logs', 'start_time_local')
    op.drop_column('domain_logs', 'end_time_local')
    op.drop_column('domain_logs', 'gathering_date_local')