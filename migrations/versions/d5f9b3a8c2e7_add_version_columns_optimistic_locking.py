"""Add version columns for optimistic locking

Revision ID: d5f9b3a8c2e7
Revises: 47d65459653b
Create Date: 2025-11-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5f9b3a8c2e7'
down_revision = '47d65459653b'
branch_label = None
depends_on = None


def upgrade():
    # Add version column to shopping_lists table
    op.add_column('shopping_lists', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    # Add version column to shopping_list_items table
    op.add_column('shopping_list_items', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    # Remove version column from shopping_list_items table
    op.drop_column('shopping_list_items', 'version')

    # Remove version column from shopping_lists table
    op.drop_column('shopping_lists', 'version')
