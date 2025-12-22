"""
Alembic migration script template.

Revision ID: 761482d8b883
Revises: 70c020ced272
Create Date: 2025-11-11 18:48:27.498945+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '761482d8b883'
down_revision: Union[str, None] = '70c020ced272'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change embedding column from VECTOR(1536) to VECTOR(384).
    This also drops existing embeddings since they are zero-padded and incorrect.
    """
    # Drop HNSW index if it exists
    op.execute('DROP INDEX IF EXISTS idx_notes_embedding_hnsw')
    
    # Drop the old embedding column
    op.drop_column('notes', 'embedding')
    
    # Add new embedding column with correct dimension
    op.add_column('notes', sa.Column('embedding', Vector(384), nullable=True))
    
    # Recreate HNSW index with correct dimension
    op.execute("""
        CREATE INDEX idx_notes_embedding_hnsw 
        ON notes 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """Revert back to VECTOR(1536) - not recommended."""
    # Drop new index
    op.execute('DROP INDEX IF EXISTS idx_notes_embedding_hnsw')
    
    # Drop the 384-dim column
    op.drop_column('notes', 'embedding')
    
    # Restore old 1536-dim column
    op.add_column('notes', sa.Column('embedding', Vector(1536), nullable=True))
    
    # Recreate old index
    op.execute("""
        CREATE INDEX idx_notes_embedding_hnsw 
        ON notes 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
