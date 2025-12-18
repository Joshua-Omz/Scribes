"""
Alembic migration script template.

Revision ID: c7cedc1c66cb
Revises: 002_create_cross_refs
Create Date: 2025-11-04 20:03:20.496306+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7cedc1c66cb'
down_revision: Union[str, None] = '002_create_cross_refs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    pass


def downgrade() -> None:
    """Revert migration changes."""
    pass
