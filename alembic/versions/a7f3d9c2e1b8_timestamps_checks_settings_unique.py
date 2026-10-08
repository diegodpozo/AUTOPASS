"""fechas text->timestamp, check constraints e indice unico de settings

Revision ID: a7f3d9c2e1b8
Revises: 9c4f2a7b1e83
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f3d9c2e1b8'
down_revision: Union[str, Sequence[str], None] = '9c4f2a7b1e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# COLUMNAS QUE PASAN DE VARCHAR A TIMESTAMP REAL (VERIFICADO: 100% DE LOS
# VALORES CASTEA SIN ERRORES; SE USAN NULLIF POR SI HAY STRINGS VACIOS).
# EN PYTHON SIGUEN VOLVIENDO COMO STRING 'YYYY-MM-DD HH:MM:SS' VIA
# models.types.DateTimeAsStr (COMPATIBILIDAD BACK/FRONT).
_FECHAS = {
    "access_logs": ["fecha_hora", "fecha_pago"],
    "reservations": ["fecha_inicio", "fecha_fin", "fecha_pago"],
    "mercadopago_payments": ["fecha_creacion", "fecha_confirmacion"],
    "points_log": ["fecha"],
}

_AFORO_NONNEG = (
    "COALESCE(capacidad_total, 0) >= 0 AND COALESCE(ocupacion_actual, 0) >= 0 AND "
    "COALESCE(capacidad_motos, 0) >= 0 AND COALESCE(ocupacion_motos, 0) >= 0 AND "
    "COALESCE(capacidad_camionetas, 0) >= 0 AND COALESCE(ocupacion_camionetas, 0) >= 0 AND "
    "COALESCE(capacidad_reservas_autos, 0) >= 0 AND COALESCE(ocupacion_reservas_autos, 0) >= 0 AND "
    "COALESCE(capacidad_reservas_motos, 0) >= 0 AND COALESCE(ocupacion_reservas_motos, 0) >= 0 AND "
    "COALESCE(capacidad_reservas_camionetas, 0) >= 0 AND COALESCE(ocupacion_reservas_camionetas, 0) >= 0 AND "
    "COALESCE(capacidad_reservas, 0) >= 0 AND COALESCE(ocupacion_reservas, 0) >= 0"
)

# (nombre, tabla, condicion) - PREVIAMENTE VERIFICADO: 0 VIOLACIONES EN DATOS REALES
_CHECKS = [
    ("ck_users_saldo_nonneg", "users", "COALESCE(saldo, 0) >= 0"),
    ("ck_users_puntos_nonneg", "users", "COALESCE(puntos_acumulados, 0) >= 0"),
    ("ck_promotions_costo_puntos_nonneg", "promotions", "COALESCE(costo_puntos, 0) >= 0"),
    ("ck_promotions_valor_descuento_pct", "promotions",
     "valor_descuento IS NULL OR valor_descuento BETWEEN 1 AND 100"),
    ("ck_settings_valor_nonneg", "settings", "COALESCE(valor, 0) >= 0"),
    ("ck_access_logs_costo_estadia_nonneg", "access_logs", "COALESCE(costo_estadia, 0) >= 0"),
    ("ck_reservations_monto_total_nonneg", "reservations", "COALESCE(monto_total, 0) >= 0"),
    ("ck_reservations_monto_reembolsado_nonneg", "reservations", "COALESCE(monto_reembolsado, 0) >= 0"),
    ("ck_reservations_orden_fechas", "reservations",
     "fecha_inicio IS NULL OR fecha_fin IS NULL OR fecha_fin >= fecha_inicio"),
    ("ck_mercadopago_payments_monto_nonneg", "mercadopago_payments", "COALESCE(monto, 0) >= 0"),
    ("ck_parking_aforo_nonneg", "parking_aforo", _AFORO_NONNEG),
]

# INDICE UNICO DE SETTINGS: (clave, COALESCE(sucursal,'')) - PERMITE VARIANTES
# POR SEDE PERO BLOQUEA DUPLICADOS EXACTOS (LOS GLOBALES CON SUCURSAL NULL
# CUENTAN COMO VALOR PROPIO). VALIDADO: 0 DUPLICADOS EN 112 FILAS ACTUALES.
_SQL_INDICE_UNICO = (
    "CREATE UNIQUE INDEX uq_settings_clave_sucursal "
    "ON settings (clave, COALESCE(sucursal, ''))"
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # 1. FECHAS VARCHAR -> TIMESTAMP (USING CAST EXPLICITO)
        for tabla, columnas in _FECHAS.items():
            for col in columnas:
                op.execute(
                    f"ALTER TABLE {tabla} ALTER COLUMN {col} "
                    f"TYPE timestamp USING NULLIF({col}, '')::timestamp"
                )
        # 2. CHECK CONSTRAINTS (SQLITE NO SOPORTA ALTER ... ADD CONSTRAINT:
        #    EN SQLITE ESTA CADENA SOLO SE USA PARA TESTS DE PARIDAD DE INDICES)
        for nombre, tabla, condicion in _CHECKS:
            op.create_check_constraint(nombre, tabla, condicion)
    # 3. INDICE UNICO DE SETTINGS (EXPRESION: SOPORTADA EN POSTGRES Y SQLITE)
    op.execute(_SQL_INDICE_UNICO)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX uq_settings_clave_sucursal")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for nombre, tabla, _condicion in reversed(_CHECKS):
            op.drop_check_constraint(nombre, tabla)
        for tabla, columnas in _FECHAS.items():
            for col in columnas:
                op.execute(
                    f"ALTER TABLE {tabla} ALTER COLUMN {col} "
                    f"type VARCHAR USING {col}::VARCHAR"
                )
