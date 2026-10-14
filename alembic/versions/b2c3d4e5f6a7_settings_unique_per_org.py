"""multi-tenant: unicidad de settings por organizacion

Revision ID: b2c3d4e5f6a7
Revises: a1c2e3f4b5d6
Create Date: 2026-10-13 13:00:00.000000

El indice unico `uq_settings_clave_sucursal` (clave + COALESCE(sucursal_id,-1))
impedia que dos organizaciones tengan su propia fila GLOBAL (sucursal_id NULL)
para la misma clave: colisionaban. Se reemplaza por
`uq_settings_clave_sucursal_org`, que agrega COALESCE(organization_id,-1) para
que cada empresa tenga su propio tarifario global aislado.

IDEMPOTENTE: usa DROP/CREATE INDEX IF (NOT) EXISTS porque `sync_schema` corre
create_all antes de Alembic (en una base nueva el indice nuevo ya existe).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1c2e3f4b5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Reemplaza el indice unico global por uno que incluye la organizacion."""
    bind = op.get_bind()
    bind.execute(sa.text("DROP INDEX IF EXISTS uq_settings_clave_sucursal"))
    bind.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_clave_sucursal_org "
        "ON settings (clave, COALESCE(sucursal_id, -1), COALESCE(organization_id, -1))"
    ))


def downgrade() -> None:
    """Vuelve al indice unico por clave+sede (single-tenant)."""
    bind = op.get_bind()
    bind.execute(sa.text("DROP INDEX IF EXISTS uq_settings_clave_sucursal_org"))
    bind.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_clave_sucursal "
        "ON settings (clave, COALESCE(sucursal_id, -1))"
    ))
