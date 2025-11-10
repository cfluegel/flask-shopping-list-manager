"""Add RevokedToken model for JWT blacklist

Revision ID: c4e8f9a2b3d1
Revises: be00b14abfb0
Create Date: 2025-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 'c4e8f9a2b3d1'
down_revision = 'be00b14abfb0'
branch_labels = None
depends_on = None


def upgrade():
    """Add revoked_tokens table for JWT token blacklist."""
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=120), nullable=False),
        sa.Column('token_type', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti')
    )

    # Create index on jti for fast lookups
    op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)


def downgrade():
    """Remove revoked_tokens table."""
    op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
