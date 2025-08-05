"""convert_meeting_type_to_table

Revision ID: b88afb1acb0e
Revises: ffc2f6fcc8bd
Create Date: 2025-08-01 19:27:46.919466

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b88afb1acb0e'
down_revision: Union[str, None] = 'ffc2f6fcc8bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Step 1: First drop the type column to remove dependency on the enum
    op.drop_column('meeting', 'type')
    
    # Step 2: Drop the old enum type 
    try:
        op.execute("DROP TYPE IF EXISTS meetingtype CASCADE")
    except Exception:
        # Ignore if the type doesn't exist or can't be dropped
        pass
    
    # Step 3: Create the meetingtype table
    op.create_table(
        'meetingtype',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title')
    )
    
    # Step 2: Insert predefined meeting types
    meeting_type_table = sa.table(
        'meetingtype',
        sa.column('id', sa.Uuid),
        sa.column('title', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    # Get current timestamp
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # Define meeting type UUIDs (consistent for data migration)
    meeting_types = [
        (uuid.UUID('11111111-1111-1111-1111-111111111111'), 'all-hands'),
        (uuid.UUID('22222222-2222-2222-2222-222222222222'), 'one-on-one'),
        (uuid.UUID('33333333-3333-3333-3333-333333333333'), 'team-meeting'),
        (uuid.UUID('44444444-4444-4444-4444-444444444444'), 'standup'),
        (uuid.UUID('55555555-5555-5555-5555-555555555555'), 'project-meeting'),
    ]
    
    op.bulk_insert(
        meeting_type_table,
        [
            {
                'id': type_id,
                'title': title,
                'created_at': now,
                'updated_at': now
            }
            for type_id, title in meeting_types
        ]
    )
    
    # Step 3: Add type_id column to meeting table
    op.add_column('meeting', sa.Column('type_id', sa.Uuid(), nullable=False,
                                       server_default=str(uuid.UUID('11111111-1111-1111-1111-111111111111'))))
    
    # Step 4: Add foreign key constraint
    op.create_foreign_key(
        'fk_meeting_type_id',
        'meeting', 'meetingtype',
        ['type_id'], ['id']
    )
    
    # Step 5: Remove the server default now that we have data
    op.alter_column('meeting', 'type_id', server_default=None)


def downgrade() -> None:
    """Downgrade database schema."""
    # Step 1: Drop foreign key constraint and type_id column
    op.drop_constraint('fk_meeting_type_id', 'meeting', type_='foreignkey')
    op.drop_column('meeting', 'type_id')
    
    # Step 2: Recreate the enum type and add back the type column
    meetingtype_enum = sa.Enum(
        'ALL_HANDS', 'ONE_ON_ONE', 'TEAM_MEETING', 'STANDUP', 'PROJECT_MEETING',
        name='meetingtype'
    )
    meetingtype_enum.create(op.get_bind())
    
    # Step 3: Add back the type column with enum and default value
    op.add_column('meeting', sa.Column('type', meetingtype_enum, nullable=False, 
                                       server_default='ALL_HANDS'))
    
    # Step 4: Drop the meetingtype table
    op.drop_table('meetingtype')
