"""reservas: foto de tarifas/duración/total al cotizar

Deja registro de con qué tarifario y cálculo quedó una reserva puntual:
  - tarifa_hora / tarifa_fraccion: tarifas unitarias vigentes en la sede.
  - tarifa_aplicada: tarifa unitaria de la modalidad (hora/día/semana/...).
  - horas_calculadas: duración cotizada en horas.
  - monto_calculado: total base cotizado (antes de descuentos).
  - descuento_pct: % de descuento por canje aplicado al pagar.
  - tarifa_fijada_en: momento en que se fijó la foto.

Revision ID: a9b8c7d6e5f4
Revises: f7a8b9c0d1e2
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega las columnas de la foto de tarifas a `reservations`."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tarifa_hora', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('tarifa_fraccion', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('tarifa_aplicada', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('horas_calculadas', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('monto_calculado', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('descuento_pct', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('tarifa_fijada_en', sa.String(), nullable=True))


def downgrade() -> None:
    """Quita las columnas de la foto de tarifas."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.drop_column('tarifa_fijada_en')
        batch_op.drop_column('descuento_pct')
        batch_op.drop_column('monto_calculado')
        batch_op.drop_column('horas_calculadas')
        batch_op.drop_column('tarifa_aplicada')
        batch_op.drop_column('tarifa_fraccion')
        batch_op.drop_column('tarifa_hora')
