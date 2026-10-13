"""quitar columnas de NOMBRE de sucursal (la referencia pasa a ser solo sucursal_id)

Revision ID: c3d4e5f6a7b8
Revises: f5a6b7c8d9e0
Create Date: 2026-10-10 01:00:00.000000

Fase final de la migracion por id de sucursales: se eliminan las columnas de
NOMBRE legacy (reservations.sucursal_nombre, users.sucursal, access_logs.sucursal,
support_tickets.sucursal, redemption_tickets.sucursal, parking_aforo.sucursal,
settings.sucursal, parking_cameras.sucursal, promotions.sucursal) y sus indices /
FKs por nombre. La unica fuente de verdad de la sede pasa a ser `sucursal_id`
(FK -> parking_branches.id), por lo que renombrar una sede solo toca
`parking_branches` y ya no requiere propagacion.

El indice compuesto `ix_access_logs_pat_tipo_suc_fecha` y el unico
`uq_settings_clave_sucursal` estaban definidos sobre la columna de NOMBRE: se
recrean sobre `sucursal_id`.

En SQLITE esta cadena solo se usa para los tests de paridad de indices: las FKs
por nombre no existen (se crean solo en postgres) y el batch_alter_table recrea
la tabla. En POSTGRES se dropean primero las FKs por nombre (b2f4e8c1a9d7).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabla, columna de NOMBRE legacy, indices a dropear, FK por nombre opcional,
#  indices a recrear sobre las columnas nuevas)
_TABLAS = [
    ("access_logs", "sucursal",
     ["ix_access_logs_sucursal", "ix_access_logs_pat_tipo_suc_fecha"], None,
     [("ix_access_logs_pat_tipo_suc_fecha",
       ["patente_detectada", "tipo_evento", "sucursal_id", "fecha_hora"])]),
    ("reservations", "sucursal_nombre", ["ix_reservations_sucursal_nombre"], None, []),
    ("users", "sucursal", [], None, []),
    ("support_tickets", "sucursal", ["ix_support_tickets_sucursal"], None, []),
    ("redemption_tickets", "sucursal", [], None, []),
    ("parking_aforo", "sucursal", ["ix_parking_aforo_sucursal_id"],
     "fk_parking_aforo_sucursal_branch", []),
    ("settings", "sucursal", [], "fk_settings_sucursal_branch", []),
    ("parking_cameras", "sucursal", [], "fk_parking_cameras_sucursal_branch", []),
    ("promotions", "sucursal", [], "fk_promotions_sucursal_branch", []),
]

_UQ_SETTINGS_NUEVO = (
    "CREATE UNIQUE INDEX uq_settings_clave_sucursal "
    "ON settings (clave, COALESCE(sucursal_id, -1))"
)
_UQ_SETTINGS_VIEJO = (
    "CREATE UNIQUE INDEX uq_settings_clave_sucursal "
    "ON settings (clave, COALESCE(sucursal, ''))"
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    # El indice unico de settings referencia la columna de NOMBRE: se recrea
    # despues sobre sucursal_id.
    op.execute("DROP INDEX IF EXISTS uq_settings_clave_sucursal")
    for tabla, col, drop_idx, fk, reindex in _TABLAS:
        with op.batch_alter_table(tabla) as b:
            for ix in drop_idx:
                b.drop_index(ix)
            if fk and postgres:
                b.drop_constraint(fk, type_="foreignkey")
            b.drop_column(col)
            for ix, cols in reindex:
                b.create_index(ix, cols)
    op.execute(_UQ_SETTINGS_NUEVO)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    op.execute("DROP INDEX IF EXISTS uq_settings_clave_sucursal")
    for tabla, col, drop_idx, fk, reindex in reversed(_TABLAS):
        with op.batch_alter_table(tabla) as b:
            for ix, _cols in reindex:
                b.drop_index(ix)
            b.add_column(sa.Column(col, sa.String(), nullable=True))
            for ix in drop_idx:
                if ix == "ix_access_logs_pat_tipo_suc_fecha":
                    b.create_index(ix, ["patente_detectada", "tipo_evento", col, "fecha_hora"])
                else:
                    b.create_index(ix, [col])
            if fk and postgres:
                b.create_foreign_key(fk, "parking_branches", [col], ["nombre"],
                                     onupdate="CASCADE", ondelete="CASCADE")
    op.execute(_UQ_SETTINGS_VIEJO)
