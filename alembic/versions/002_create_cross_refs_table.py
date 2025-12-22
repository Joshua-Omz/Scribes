"""create cross_refs table

Revision ID: 002_create_cross_refs
Revises: 001_notes_scripture_refs
Create Date: 2025-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002_create_cross_refs'
down_revision: Union[str, None] = '001_notes_scripture_refs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cross_refs table."""
    # Check if table already exists
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' AND table_name='cross_refs'
    """))
    
    if not result.fetchone():
        # Create cross_refs table
        op.create_table(
            'cross_refs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('note_id', sa.Integer(), nullable=False),
            sa.Column('other_note_id', sa.Integer(), nullable=False),
            sa.Column('reference_type', sa.String(length=50), nullable=False, server_default='related'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_auto_generated', sa.String(length=20), nullable=False, server_default='manual'),
            sa.Column('confidence_score', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['other_note_id'], ['notes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for better query performance
        op.create_index('ix_cross_refs_note_id', 'cross_refs', ['note_id'])
        op.create_index('ix_cross_refs_other_note_id', 'cross_refs', ['other_note_id'])
        op.create_index('ix_cross_refs_reference_type', 'cross_refs', ['reference_type'])
        op.create_index('ix_cross_refs_is_auto_generated', 'cross_refs', ['is_auto_generated'])


def downgrade() -> None:
    """Drop cross_refs table."""
    op.drop_index('ix_cross_refs_is_auto_generated', table_name='cross_refs')
    op.drop_index('ix_cross_refs_reference_type', table_name='cross_refs')
    op.drop_index('ix_cross_refs_other_note_id', table_name='cross_refs')
    op.drop_index('ix_cross_refs_note_id', table_name='cross_refs')
    op.drop_table('cross_refs')
