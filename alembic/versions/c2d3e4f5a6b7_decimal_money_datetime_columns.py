"""Use fixed-point money and datetime columns.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""
from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


_MONEY_COLUMNS = {
    "reservations": (
        "monto_total",
        "monto_reembolsado",
        "tarifa_hora",
        "tarifa_fraccion",
        "tarifa_aplicada",
        "monto_calculado",
    ),
    "users": ("saldo",),
    "settings": ("valor",),
    "access_logs": ("costo_estadia",),
    "mercadopago_payments": ("monto",),
}

_DATETIME_COLUMNS = {
    "redemption_tickets": ("created_at", "fecha_uso"),
    "organizations": ("created_at",),
    "parking_aforo": ("ultima_actualizacion",),
}


def _create_settings_unique_index():
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_clave_sucursal_org "
        "ON settings (clave, COALESCE(sucursal_id, -1), COALESCE(organization_id, -1))"
    )


def _alter_datetime_columns(table, columns, source_type, target_type):
    dialect = op.get_bind().dialect.name
    sqlite_backups = {}
    if dialect == "sqlite" and isinstance(target_type, sa.DateTime):
        for column in columns:
            backup = f"_c2d3e4_{column}"
            sqlite_backups[column] = backup
            op.add_column(table, sa.Column(backup, sa.String(), nullable=True))
            op.execute(sa.text(f'UPDATE "{table}" SET "{backup}" = "{column}"'))

    with op.batch_alter_table(table) as batch:
        for column in columns:
            postgresql_using = {}
            if dialect == "postgresql":
                cast_type = (
                    "timestamp without time zone"
                    if isinstance(target_type, sa.DateTime)
                    else "text"
                )
                postgresql_using["postgresql_using"] = f'"{column}"::{cast_type}'
            batch.alter_column(
                column,
                existing_type=source_type,
                type_=target_type,
                existing_nullable=True,
                **postgresql_using,
            )

    for column, backup in sqlite_backups.items():
        # SQLite's batch CAST to DATETIME keeps only the year; restore the original text.
        op.execute(sa.text(f'UPDATE "{table}" SET "{column}" = "{backup}"'))
        with op.batch_alter_table(table) as batch:
            batch.drop_column(backup)


def upgrade():
    is_postgresql = op.get_bind().dialect.name == "postgresql"
    for table, columns in _MONEY_COLUMNS.items():
        with op.batch_alter_table(table) as batch:
            for column in columns:
                postgresql_using = (
                    {"postgresql_using": f'"{column}"::numeric(12, 2)'}
                    if is_postgresql
                    else {}
                )
                batch.alter_column(
                    column,
                    existing_type=sa.Float(),
                    type_=sa.Numeric(12, 2),
                    existing_nullable=True,
                    **postgresql_using,
                )
        for column in columns:
            op.execute(
                sa.text(f"UPDATE {table} SET {column} = ROUND({column}, 2) "
                        f"WHERE {column} IS NOT NULL")
            )
    for table, columns in _DATETIME_COLUMNS.items():
        _alter_datetime_columns(table, columns, sa.String(), sa.DateTime())

    _create_settings_unique_index()


def downgrade():
    is_postgresql = op.get_bind().dialect.name == "postgresql"
    for table, columns in reversed(tuple(_DATETIME_COLUMNS.items())):
        _alter_datetime_columns(table, columns, sa.DateTime(), sa.String())

    for table, columns in reversed(tuple(_MONEY_COLUMNS.items())):
        with op.batch_alter_table(table) as batch:
            for column in columns:
                postgresql_using = (
                    {"postgresql_using": f'"{column}"::double precision'}
                    if is_postgresql
                    else {}
                )
                batch.alter_column(
                    column,
                    existing_type=sa.Numeric(12, 2),
                    type_=sa.Float(),
                    existing_nullable=True,
                    **postgresql_using,
                )
    _create_settings_unique_index()
