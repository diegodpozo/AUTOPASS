"""create support_ticket_messages table

Revision ID: e5a2b8c1d937
Revises: d4f7c8e2a190
Create Date: 2026-08-17 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e5a2b8c1d937'
down_revision: Union[str, Sequence[str], None] = 'd4f7c8e2a190'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_ticket_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('support_tickets.id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('support_ticket_messages')
