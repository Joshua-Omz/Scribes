"""
Add HNSW index for embedding vector search performance.

HNSW (Hierarchical Navigable Small World) is an approximate nearest neighbor
search algorithm that significantly improves query performance for vector
similarity searches at the cost of some accuracy.

Revision ID: 70c020ced272
Revises: 31ac95978827
Create Date: 2025-11-09 17:20:24.108625+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70c020ced272'
down_revision: Union[str, None] = '31ac95978827'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Apply migration changes.
    
    Creates an HNSW index on the embedding column for fast vector searches.
    Parameters:
    - m=16: Maximum number of connections per layer (higher = better recall, more memory)
    - ef_construction=64: Size of dynamic candidate list for construction (higher = better quality, slower build)
    """
    # Create HNSW index using vector_cosine_ops for cosine distance
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_embedding_hnsw
        ON notes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def downgrade() -> None:
    """Revert migration changes."""
    op.execute("DROP INDEX IF EXISTS idx_notes_embedding_hnsw;")
