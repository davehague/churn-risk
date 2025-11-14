"""make ticket content nullable

Revision ID: b4fc6e577219
Revises: 4aa56adc37c1
Create Date: 2025-11-14 12:58:21.444514

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b4fc6e577219'
down_revision = '4aa56adc37c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make ticket content nullable (some HubSpot tickets have no content)
    op.alter_column('tickets', 'content',
               existing_type=sa.TEXT(),
               nullable=True)


def downgrade() -> None:
    # Revert ticket content back to non-nullable
    op.alter_column('tickets', 'content',
               existing_type=sa.TEXT(),
               nullable=False)
