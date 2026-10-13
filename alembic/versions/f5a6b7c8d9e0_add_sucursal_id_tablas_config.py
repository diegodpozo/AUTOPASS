"""agregar sucursal_id (FK a parking_branches.id) en las tablas de configuracion por nombre

Revision ID: f5a6b7c8d9e0
Revises: d1e2f3a4b5c6
Create Date: 2026-10-09 02:00:00.000000

Fase 4 de la migracion por id de sucursales: aforo, settings, camaras y
promociones son las ultimas tablas que referencian la sede por NOMBRE (FK por
nombre con CASCADE de b2f4e8c1a9d7). Se agrega `sucursal_id` (FK ->
parking_branches.id) con backfill del id derivado del nombre actual, igual que
la Fase 1. Las filas GLOBALES (sucursal NULL) quedan con sucursal_id NULL.

La columna de nombre legacy se mantiene como cache de display: se sigue
propagando en rename SOLO para no desactualizar las vistas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabla, columna de NOMBRE legacy de la que se deriva el id)
_TABLAS = [
    ("parking_aforo", "sucursal"),
    ("settings", "sucursal"),
    ("parking_cameras", "sucursal"),
    ("promotions", "sucursal"),
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    for tabla, _col in _TABLAS:
        op.add_column(tabla, sa.Column("sucursal_id", sa.Integer(), nullable=True))
        op.create_index(f"ix_{tabla}_sucursal_id", tabla, ["sucursal_id"])
    if bind.dialect.name == "postgresql":
        # BACKFILL: derivar el id desde el nombre actual de cada fila.
        for tabla, col in _TABLAS:
            op.execute(sa.text(
                f"UPDATE {tabla} SET sucursal_id = (SELECT b.id FROM parking_branches b "
                f"WHERE b.nombre = {tabla}.{col})"
            ))
        for tabla, _col in _TABLAS:
            op.create_foreign_key(
                f"fk_{tabla}_sucursal_id_branch", tabla, "parking_branches",
                ["sucursal_id"], ["id"], onupdate="CASCADE",
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for tabla, _col in reversed(_TABLAS):
            op.drop_constraint(f"fk_{tabla}_sucursal_id_branch", tabla, type_="foreignkey")
    for tabla, _col in reversed(_TABLAS):
        op.drop_index(f"ix_{tabla}_sucursal_id", table_name=tabla)
        op.drop_column(tabla, "sucursal_id")