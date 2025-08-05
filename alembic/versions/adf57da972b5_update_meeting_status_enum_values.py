"""update meeting status enum values

Revision ID: adf57da972b5
Revises: b88afb1acb0e
Create Date: 2025-08-05 02:06:08.426482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adf57da972b5'
down_revision: Union[str, None] = 'b88afb1acb0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Convert column to text temporarily
    op.execute("ALTER TABLE meeting ALTER COLUMN status TYPE text")
    
    # Update any existing values to match new enum values
    op.execute("""
        UPDATE meeting 
        SET status = CASE 
            WHEN status = 'PENDING' THEN 'NEW'
            WHEN status = 'CONFIRMED' THEN 'APPROVED'
            WHEN status = 'CANCELLED' THEN 'CANCELED'
            WHEN status = 'COMPLETED' THEN 'APPROVED'
            ELSE 'NEW'
        END;
    """)
    
    # Drop old enum and create new one
    op.execute("DROP TYPE meetingstatus")
    new_meetingstatus = sa.Enum('NEW', 'APPROVED', 'CANCELED', name='meetingstatus')
    new_meetingstatus.create(op.get_bind())
    
    # Convert column back to enum
    op.execute("ALTER TABLE meeting ALTER COLUMN status TYPE meetingstatus USING status::meetingstatus")


def downgrade() -> None:
    """Downgrade database schema."""
    # Convert back to original enum values (from the initial migration)
    op.execute("ALTER TABLE meeting ALTER COLUMN status TYPE text")
    op.execute("DROP TYPE meetingstatus")
    
    # Recreate original enum
    old_meetingstatus = sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', name='meetingstatus')
    old_meetingstatus.create(op.get_bind())
    
    # Alter the column back to original enum
    op.execute("ALTER TABLE meeting ALTER COLUMN status TYPE meetingstatus USING status::meetingstatus")
