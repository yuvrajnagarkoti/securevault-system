"""add account lockout columns to users table

Revision ID: 001_account_lockout
Revises: 
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_account_lockout'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add failed_attempts and locked_until columns for account lockout."""
    # Use batch mode for compatibility and add columns if they don't already exist
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('locked_until', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    """Remove lockout columns."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_attempts')
