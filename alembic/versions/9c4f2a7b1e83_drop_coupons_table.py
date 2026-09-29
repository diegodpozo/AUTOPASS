"""drop coupons table

Revision ID: 9c4f2a7b1e83
Revises: 8b3e9e815c78
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c4f2a7b1e83'
down_revision: Union[str, Sequence[str], None] = '8b3e9e815c78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # La tabla `coupons` quedo sin modelo ORM (su concepto lo cubre
    # `redemption_tickets`): se elimina para restaurar la paridad
    # modelo<->alembic exigida por tests/test_schema_parity_p2.py.
    op.drop_index('ix_coupons_codigo', table_name='coupons')
    op.drop_table('coupons')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=True),
        sa.Column('descuento_porcentaje', sa.Integer(), nullable=True),
        sa.Column('fecha_expiracion', sa.String(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_coupons_codigo', 'coupons', ['codigo'], unique=True)
