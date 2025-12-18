"""
Create background_jobs table for tracking async task execution.

Revision ID: fedd9ae2d5e7
Revises: 761482d8b883
Create Date: 2025-11-18 00:29:28.990673+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'fedd9ae2d5e7'
down_revision: Union[str, None] = '761482d8b883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create background_jobs table
    op.create_table(
        'background_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(length=100), nullable=False),
        
        # Status tracking
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        
        # Progress tracking
        sa.Column('progress_percent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_items', sa.Integer(), nullable=True),
        sa.Column('processed_items', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=True, server_default='0'),
        
        # Results and errors
        sa.Column('result_data', JSONB, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_background_jobs_job_id', 'background_jobs', ['job_id'], unique=True)
    op.create_index('idx_background_jobs_user_status', 'background_jobs', ['user_id', 'status'])
    op.create_index('idx_background_jobs_created_at', 'background_jobs', ['created_at'])


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_index('idx_background_jobs_created_at', table_name='background_jobs')
    op.drop_index('idx_background_jobs_user_status', table_name='background_jobs')
    op.drop_index('idx_background_jobs_job_id', table_name='background_jobs')
    op.drop_table('background_jobs')
