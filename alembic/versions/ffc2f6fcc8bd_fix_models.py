"""fix models

Revision ID: ffc2f6fcc8bd
Revises: c74db799c2dd
Create Date: 2025-06-30 11:35:12.999426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ffc2f6fcc8bd"
down_revision: Union[str, None] = "c74db799c2dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
