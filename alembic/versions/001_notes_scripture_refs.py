"""add scripture_refs column to notes table

Revision ID: 001_notes_scripture_refs
Revises: 
Create Date: 2025-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_notes_scripture_refs'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scripture_refs column and remove scripture_tags if it exists."""
    # Check if scripture_tags exists and drop it
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='notes' AND column_name='scripture_tags'
    """))
    if result.fetchone():
        op.drop_column('notes', 'scripture_tags')
    
    # Check if scripture_refs already exists before adding it
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='notes' AND column_name='scripture_refs'
    """))
    if not result.fetchone():
        op.add_column('notes', sa.Column('scripture_refs', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Revert scripture_refs back to scripture_tags."""
    op.drop_column('notes', 'scripture_refs')
    op.add_column('notes', sa.Column('scripture_tags', sa.String(length=255), nullable=True))
