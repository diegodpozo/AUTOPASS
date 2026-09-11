"""add_tipo_vehiculo_to_reservations

Revision ID: a4c8d2e3f5b6
Revises: d3b7e1a9c2f0
Create Date: 2026-09-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4c8d2e3f5b6'
down_revision: Union[str, Sequence[str], None] = 'd3b7e1a9c2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo_vehiculo', sa.String(), nullable=True, server_default='Auto'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.drop_column('tipo_vehiculo')