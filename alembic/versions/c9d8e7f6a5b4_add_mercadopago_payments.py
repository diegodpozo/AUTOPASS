"""add mercadopago_payments table

Revision ID: c9d8e7f6a5b4
Revises: a3b4c5d6e7f8
Create Date: 2026-09-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6a5b4'
down_revision: Union[str, Sequence[str], None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'mercadopago_payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('reserva_id', sa.Integer(), sa.ForeignKey('reservations.id'), nullable=True),
        sa.Column('access_log_id', sa.Integer(), sa.ForeignKey('access_logs.id'), nullable=True),
        sa.Column('redemption_ticket_id', sa.Integer(), nullable=True),
        sa.Column('patente', sa.String(), nullable=True),
        sa.Column('monto', sa.Float(), nullable=False),
        sa.Column('moneda', sa.String(), nullable=True),
        sa.Column('external_reference', sa.String(), nullable=True),
        sa.Column('preference_id', sa.String(), nullable=True),
        sa.Column('payment_id', sa.String(), nullable=True),
        sa.Column('estado', sa.String(), nullable=True),
        sa.Column('mp_status', sa.String(), nullable=True),
        sa.Column('fecha_creacion', sa.String(), nullable=True),
        sa.Column('fecha_confirmacion', sa.String(), nullable=True),
    )
    op.create_index('ix_mercadopago_payments_external_reference', 'mercadopago_payments', ['external_reference'], unique=True)
    op.create_index('ix_mercadopago_payments_user_id', 'mercadopago_payments', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_mercadopago_payments_user_id', table_name='mercadopago_payments')
    op.drop_index('ix_mercadopago_payments_external_reference', table_name='mercadopago_payments')
    op.drop_table('mercadopago_payments')