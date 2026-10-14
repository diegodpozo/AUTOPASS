"""multi-tenant: unicidad de nombre de sucursal por organizacion

Revision ID: f7a8b9c0d1e2
Revises: b2c3d4e5f6a7
Create Date: 2026-10-13 21:00:00.000000

El nombre de sucursal era unico GLOBAL (`ix_parking_branches_nombre` unique),
lo que impedia que una empresa nueva creara una sede con un nombre ya usado por
otra. Se pasa a unicidad POR ORGANIZACION:
  - `ix_parking_branches_nombre`: indice simple (NO unico) para busquedas.
  - `uq_parking_branches_nombre_org`: unico sobre (nombre, COALESCE(organization_id,-1)).

IDEMPOTENTE: usa DROP/CREATE INDEX IF (NOT) EXISTS porque `sync_schema` corre
create_all antes de Alembic (en una base nueva los indices nuevos ya existen).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """El nombre deja de ser unico global y pasa a ser unico por organizacion."""
    bind = op.get_bind()
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_parking_branches_nombre"))
    bind.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_parking_branches_nombre "
        "ON parking_branches (nombre)"
    ))
    bind.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_parking_branches_nombre_org "
        "ON parking_branches (nombre, COALESCE(organization_id, -1))"
    ))


def downgrade() -> None:
    """Vuelve al nombre de sucursal unico GLOBAL (single-tenant)."""
    bind = op.get_bind()
    bind.execute(sa.text("DROP INDEX IF EXISTS uq_parking_branches_nombre_org"))
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_parking_branches_nombre"))
    bind.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_parking_branches_nombre "
        "ON parking_branches (nombre)"
    ))
