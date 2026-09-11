"""add_metodo_pago_to_reservations

Revision ID: d3b7e1a9c2f0
Revises: e6f7a8b9c0d1
Create Date: 2026-09-08 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b7e1a9c2f0'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('metodo_pago', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.drop_column('metodo_pago')