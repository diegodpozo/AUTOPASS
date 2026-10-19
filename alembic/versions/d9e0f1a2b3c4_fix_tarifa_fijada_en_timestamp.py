"""reservas: tarifa_fijada_en vuelve a ser TIMESTAMP

Corrige el tipo de `reservations.tarifa_fijada_en` para que coincida con el resto
de columnas de fecha del proyecto (fecha_inicio / fecha_fin / fecha_pago), que en
PostgreSQL son `timestamp without time zone`.

La migración original (a9b8c7d6e5f4) creó la columna como `sa.String()` (VARCHAR),
pero el modelo (`models/reservation.py`) la declara `DateTimeAsStr`, cuyo `impl`
es `DateTime`. Ese desajuste modelo <-> base de datos era la causa raíz del error
`'str' object has no attribute 'strftime'` al leer reservas con la foto de tarifa.

Revision ID: d9e0f1a2b3c4
Revises: a9b8c7d6e5f4
Create Date: 2026-10-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, Sequence[str], None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convierte tarifa_fijada_en de VARCHAR a TIMESTAMP (mismo tipo que las demás fechas)."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.alter_column(
            'tarifa_fijada_en',
            existing_type=sa.String(),
            type_=sa.DateTime(),
            existing_nullable=True,
            postgresql_using='tarifa_fijada_en::timestamp',
        )


def downgrade() -> None:
    """Revierte tarifa_fijada_en a VARCHAR con el formato canonico 'YYYY-MM-DD HH:MM:SS'."""
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.alter_column(
            'tarifa_fijada_en',
            existing_type=sa.DateTime(),
            type_=sa.String(),
            existing_nullable=True,
            postgresql_using="to_char(tarifa_fijada_en, 'YYYY-MM-DD HH24:MI:SS')",
        )
