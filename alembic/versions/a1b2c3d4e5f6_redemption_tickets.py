"""redemption tickets y tipo de canje en promotions

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('promotions', sa.Column('tipo_canje', sa.String(), nullable=True, server_default='voucher'))
    op.add_column('promotions', sa.Column('valor_descuento', sa.Integer(), nullable=True))

    op.create_table(
        'redemption_tickets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('promotion_id', sa.Integer(), sa.ForeignKey('promotions.id'), nullable=True),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=True),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('tipo_canje', sa.String(), nullable=True, server_default='voucher'),
        sa.Column('valor_descuento', sa.Integer(), nullable=True),
        sa.Column('icono', sa.String(), nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.Column('estado', sa.String(), nullable=True, server_default='VIGENTE'),
        sa.Column('qr_data', sa.String(), nullable=True),
        sa.Column('observacion', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('fecha_uso', sa.String(), nullable=True),
        sa.Column('reserva_id', sa.Integer(), nullable=True),
    )
    op.create_index('ix_redemption_tickets_codigo', 'redemption_tickets', ['codigo'], unique=True)
    op.create_index('ix_redemption_tickets_user_id', 'redemption_tickets', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_redemption_tickets_user_id', table_name='redemption_tickets')
    op.drop_index('ix_redemption_tickets_codigo', table_name='redemption_tickets')
    op.drop_table('redemption_tickets')
    op.drop_column('promotions', 'valor_descuento')
    op.drop_column('promotions', 'tipo_canje')
