"""Add unique constraint to ticket external_id

Revision ID: 9f1cb95f1d24
Revises: c08085465bad
Create Date: 2025-11-08 22:12:23.144446

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f1cb95f1d24'
down_revision = 'c08085465bad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old non-unique index
    op.drop_index('ix_tickets_tenant_external', table_name='tickets')

    # Create a unique index on (tenant_id, external_id)
    op.create_index(
        'ix_tickets_tenant_external',
        'tickets',
        ['tenant_id', 'external_id'],
        unique=True
    )


def downgrade() -> None:
    # Drop the unique index
    op.drop_index('ix_tickets_tenant_external', table_name='tickets')

    # Recreate the old non-unique index
    op.create_index(
        'ix_tickets_tenant_external',
        'tickets',
        ['tenant_id', 'external_id'],
        unique=False
    )
