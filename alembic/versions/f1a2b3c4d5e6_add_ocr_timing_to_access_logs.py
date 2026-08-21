"""add ocr_time and backend_time to access_logs

Revision ID: f1a2b3c4d5e6
Revises: e5a2b8c1d937
Create Date: 2026-08-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e5a2b8c1d937'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('access_logs', sa.Column('ocr_time', sa.Float(), nullable=True))
    op.add_column('access_logs', sa.Column('backend_time', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('access_logs', 'backend_time')
    op.drop_column('access_logs', 'ocr_time')
