"""add adjunto fields to support_ticket_messages

Revision ID: a3b4c5d6e7f8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('support_ticket_messages', sa.Column('adjunto_url', sa.String(), nullable=True))
    op.add_column('support_ticket_messages', sa.Column('adjunto_nombre', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('support_ticket_messages', 'adjunto_nombre')
    op.drop_column('support_ticket_messages', 'adjunto_url')
