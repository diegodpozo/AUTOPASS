"""fk de sucursal hacia parking_branches.nombre

Revision ID: b2f4e8c1a9d7
Revises: a7f3d9c2e1b8
Create Date: 2026-10-08 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f4e8c1a9d7'
down_revision: Union[str, Sequence[str], None] = 'a7f3d9c2e1b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# FK DE SUCURSAL -> parking_branches.nombre (nombre es UNIQUE -> PK natural de sede).
# - ON UPDATE CASCADE: rename_branch renombra la sede y las 4 tablas de config siguen.
# - ON DELETE CASCADE: delete_branch (que ya valida ocupacion y reservas) limpia sola
#   la config asociada (aforo/tarifas/camaras/promos) en lugar de dejar huespedes.
# VERIFICADO ANTES DE APLICAR: 0 HUERFANOS EN LAS 4 TABLAS (2026-10-08).
_FKS = [
    ("fk_parking_aforo_sucursal_branch", "parking_aforo"),
    ("fk_settings_sucursal_branch", "settings"),
    ("fk_parking_cameras_sucursal_branch", "parking_cameras"),
    ("fk_promotions_sucursal_branch", "promotions"),
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # SQLITE NO SOPORTA ALTER ... ADD CONSTRAINT: EN SQLITE ESTA CADENA SOLO
        # SE USA PARA TESTS DE PARIDAD DE INDICES (Y AHÍ EL FK SE CREA VIA
        # create_all CON LA DEFINICION DEL MODELO).
        for nombre, tabla in _FKS:
            op.create_foreign_key(
                nombre, tabla, "parking_branches",
                ["sucursal"], ["nombre"],
                onupdate="CASCADE", ondelete="CASCADE",
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for nombre, tabla in reversed(_FKS):
            op.drop_constraint(nombre, tabla, type_="foreignkey")