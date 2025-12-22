"""
Alembic migration script template.

Revision ID: 31ac95978827
Revises: c7cedc1c66cb
Create Date: 2025-11-07 13:58:49.152397+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '31ac95978827'
down_revision: Union[str, None] = 'c7cedc1c66cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.add_column('notes', sa.Column('embedding', Vector(1536), nullable=True))
    op.execute('CREATE INDEX IF NOT EXISTS idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);')


def downgrade() -> None:
    """Revert migration changes."""
    op.execute('DROP INDEX IF EXISTS idx_notes_embedding;')
    op.drop_column('notes', 'embedding')
    op.execute('DROP EXTENSION IF EXISTS vector;')
