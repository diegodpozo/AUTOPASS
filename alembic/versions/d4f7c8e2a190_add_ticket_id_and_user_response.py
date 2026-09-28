"""add ticket_id to notifications and user_response to support_tickets

Revision ID: d4f7c8e2a190
Revises: b7e3a1d2c4f5
Create Date: 2026-08-17 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4f7c8e2a190'
down_revision: Union[str, Sequence[str], None] = 'b7e3a1d2c4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user_notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('support_tickets.id', name='fk_user_notifications_ticket_id'), nullable=True))
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_response', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.drop_column('user_response')
    with op.batch_alter_table('user_notifications', schema=None) as batch_op:
        batch_op.drop_column('ticket_id')
