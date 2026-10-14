"""multi-tenant: tabla organizations + organization_id en tablas raiz

Revision ID: a1c2e3f4b5d6
Revises: c4d5e6f7a8b9
Create Date: 2026-10-13 12:00:00.000000

Introduce el concepto de ORGANIZACION (empresa). Cada Admin General administra
una organizacion aislada. Se agrega `organization_id` (FK -> organizations.id)
en las tablas raiz: users, parking_branches, settings, parking_aforo y
promotions. El resto de las tablas se aislaran a traves de su sucursal o usuario.

Backfill: se crea la organizacion principal "AUTOPASS" (a la que pertenecen los
datos ya existentes y el sitio publico) y se asigna a todas las filas actuales.

La migracion es IDEMPOTENTE (guarda con inspector) porque `sync_schema` ejecuta
create_all antes de Alembic: en una base nueva las tablas/columnas ya existen y
solo hay que completarlas/backfillear.
"""
import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2e3f4b5d6'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tablas raiz que reciben organization_id (columna, nombre del indice, nombre de la FK)
_TABLAS = [
    ("users", "ix_users_organization_id", "fk_users_organization_id_org"),
    ("parking_branches", "ix_parking_branches_organization_id", "fk_parking_branches_organization_id_org"),
    ("settings", "ix_settings_organization_id", "fk_settings_organization_id_org"),
    ("parking_aforo", "ix_parking_aforo_organization_id", "fk_parking_aforo_organization_id_org"),
    ("promotions", "ix_promotions_organization_id", "fk_promotions_organization_id_org"),
]

PRINCIPAL = "AUTOPASS"


def _has_table(bind, tabla):
    return sa.inspect(bind).has_table(tabla)


def _has_column(bind, tabla, columna):
    return any(c["name"] == columna for c in sa.inspect(bind).get_columns(tabla))


def _has_index(bind, tabla, indice):
    return any(i["name"] == indice for i in sa.inspect(bind).get_indexes(tabla))


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    es_pg = bind.dialect.name == "postgresql"

    # 1) TABLA ORGANIZATIONS
    if not _has_table(bind, "organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(), nullable=True),
            sa.Column("es_principal", sa.Boolean(), nullable=True),
            sa.Column("activa", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=True),
        )
    if not _has_index(bind, "organizations", "ix_organizations_nombre"):
        op.create_index("ix_organizations_nombre", "organizations", ["nombre"], unique=True)

    # Agrega organization_id en cada tabla raiz (idempotente) + FK en Postgres.
    for tabla, ix_name, fk_name in _TABLAS:
        if not _has_column(bind, tabla, "organization_id"):
            op.add_column(tabla, sa.Column("organization_id", sa.Integer(), nullable=True))
        if not _has_index(bind, tabla, indice=ix_name):
            op.create_index(ix_name, tabla, ["organization_id"])
        if bind.dialect.name == "postgresql":
            fks = {fk["name"] for fk in sa.inspect(bind).get_foreign_keys(tabla)}
            if fk_name not in fks:
                op.create_foreign_key(fk_name, tabla, "organizations", ["organization_id"], ["id"],
                                      onupdate="CASCADE")

    # Backfill: crear la organizacion principal (si no existe) y asignarla a todo lo previo.
    org_id = bind.execute(
        sa.text("SELECT id FROM organizations WHERE nombre = :n"), {"n": PRINCIPAL}
    ).scalar()
    if org_id is None:
        bind.execute(
            sa.text(
                "INSERT INTO organizations (nombre, es_principal, activa, created_at) "
                "VALUES (:n, :p, :a, :c)"
            ),
            {"n": PRINCIPAL, "p": True, "a": True, "c": datetime.datetime.now().isoformat()},
        )
        org_id = bind.execute(
            sa.text("SELECT id FROM organizations WHERE nombre = :n"), {"n": PRINCIPAL}
        ).scalar()

    for tabla, _ix, _fk in _TABLAS:
        bind.execute(
            sa.text(f"UPDATE {tabla} SET organization_id = :oid WHERE organization_id IS NULL"),
            {"oid": org_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    for tabla, ix, fk in reversed(_TABLAS):
        if bind.dialect.name == "postgresql":
            fks = {f["name"] for f in sa.inspect(bind).get_foreign_keys(tabla)}
            if fk in fks:
                op.drop_constraint(fk, tabla, type_="foreignkey")
        if _has_index(bind, tabla, ix):
            op.drop_index(ix, table_name=tabla)
        if _has_column(bind, tabla, "organization_id"):
            op.drop_column(tabla, "organization_id")
    if _has_table(bind, "organizations"):
        op.drop_table("organizations")
