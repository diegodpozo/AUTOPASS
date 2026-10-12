"""agregar sucursal_id (FK a parking_branches.id) en las tablas dependientes por nombre

Revision ID: d1e2f3a4b5c6
Revises: b2f4e8c1a9d7
Create Date: 2026-10-09 01:00:00.000000

Fase 1 de la migración por id de sucursales: las tablas que hoy referencian la
sede por NOMBRE (string plano, sin FK) pasan a tener ademas `sucursal_id`
(FK -> parking_branches.id), respaldo con el id derivado del nombre actual.

La columna de nombre legacy se mantiene mientras las lecturas migran por tabla.
Al terminar, renombrar una sede solo tocara `parking_branches` (Fase 3 quita
la propagacion de nombre y esta columna deja de ser fuente de verdad).

ON UPDATE CASCADE es inocuo (el id nunca cambia) y se deja por coherencia.
ON DELETE NO CASCADE: borrar una sede no debe arrastrar reservas/usuarios/logs/tickets.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'b2f4e8c1a9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabla, columna de NOMBRE legacy de la que se deriva el id)
_TABLAS = [
    ("reservations", "sucursal_nombre"),
    ("users", "sucursal"),
    ("access_logs", "sucursal"),
    ("support_tickets", "sucursal"),
    ("redemption_tickets", "sucursal"),
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    for tabla, _col in _TABLAS:
        op.add_column(tabla, sa.Column("sucursal_id", sa.Integer(), nullable=True))
        op.create_index(f"ix_{tabla}_sucursal_id", tabla, ["sucursal_id"])
    if bind.dialect.name == "postgresql":
        # BACKFILL: derivar el id desde el nombre actual de cada fila.
        # SQLITE (solo usa la cadena para tests de paridad de indices) no soporta
        # UPDATE ... FROM ni ALTER ADD CONSTRAINT: queda sin FK, igual que las
        # otras FKs por nombre que ya existían.
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