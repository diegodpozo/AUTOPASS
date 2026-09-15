"""add_origen_to_reservations

Revision ID: b5c9d1e2f3a4
Revises: a4c8d2e3f5b6
Create Date: 2026-09-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c9d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a4c8d2e3f5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('origen', sa.String(), nullable=True, server_default='cliente'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.drop_column('origen')