"""
Create note_chunks table for chunked note storage with embeddings.

This enables token-aware RAG with better retrieval accuracy for the AI assistant.
Each note is split into chunks, and each chunk gets its own embedding vector.

Revision ID: a1b2c3d4e5f6
Revises: fedd9ae2d5e7
Create Date: 2025-11-23 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fedd9ae2d5e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create note_chunks table
    op.create_table(
        'note_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('chunk_idx', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        
        # 384-dimensional embedding vector (matches all-MiniLM-L6-v2)
        sa.Column('embedding', Vector(384), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_note_chunks_note_id', 'note_chunks', ['note_id'])
    op.create_index('idx_note_chunks_note_chunk', 'note_chunks', ['note_id', 'chunk_idx'], unique=True)
    
    # Create vector similarity search index using HNSW
    # HNSW is more efficient than IVFFlat for < 1M vectors
    # m=16 (connections per layer), ef_construction=64 (build-time accuracy)
    op.execute("""
        CREATE INDEX idx_note_chunks_embedding_hnsw 
        ON note_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_index('idx_note_chunks_embedding_hnsw', table_name='note_chunks')
    op.drop_index('idx_note_chunks_note_chunk', table_name='note_chunks')
    op.drop_index('idx_note_chunks_note_id', table_name='note_chunks')
    op.drop_table('note_chunks')

