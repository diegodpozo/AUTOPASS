"""add user_sessions table

Revision ID: b7e3a1d2c4f5
Revises: c833a3129266
Create Date: 2026-08-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e3a1d2c4f5'
down_revision: Union[str, Sequence[str], None] = 'c833a3129266'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_device_id', 'user_sessions', ['device_id'])
    op.create_index('ix_user_sessions_last_login_at', 'user_sessions', ['last_login_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_sessions_last_login_at', table_name='user_sessions')
    op.drop_index('ix_user_sessions_device_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_table('user_sessions')
