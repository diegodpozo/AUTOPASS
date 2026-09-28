"""initial_schema - BASELINE REAL (P2 A4)

Revision ID: c833a3129266
Revises:
Create Date: 2026-08-06 10:26:54.256665

Baseline auténtico: materializa el esquema del punto de partida directamente en
esta migración inicial, de modo que ``alembic upgrade head`` sea reproducible
desde una base de datos vacía SIN depender de ``Base.metadata.create_all``.

Qué contiene: las tablas base que NINGUNA migración posterior crea. Las tablas
creadas por migraciones incrementales (user_sessions, support_ticket_messages,
redemption_tickets, mercadopago_payments) NO se declaran aquí; las columnas que
agregan migraciones posteriores (ticket_id, user_response, ocr_time,
metodo_pago, tipo_vehiculo, origen, reservas de aforo/floors, direccion/lat/lng
de promociones/redemptions) y los índices de la migración 49a240f0fc25 tampoco.

El resultado final de la cadena c833->head es idéntico a ``create_all`` de los
modelos (criterio P2 de AUDITORIA_DATOS_MIGRACIONES).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c833a3129266'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea el esquema base (punto de partida)."""

    # USERS
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=True),
        sa.Column('apellido', sa.String(), nullable=True),
        sa.Column('dni', sa.String(), nullable=True),
        sa.Column('telefono', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('patente', sa.String(), nullable=True),
        sa.Column('direccion', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('rol', sa.String(), nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.Column('puntos_acumulados', sa.Integer(), nullable=True),
        sa.Column('saldo', sa.Float(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_dni', 'users', ['dni'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # VEHICLES (ix_vehicles_user_id lo crea 49a240f0fc25)
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('patente', sa.String(), nullable=True),
        sa.Column('marca_modelo', sa.String(), nullable=True),
        sa.Column('tipo', sa.String(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vehicles_patente', 'vehicles', ['patente'], unique=True)

    # POINTS LOG
    op.create_table(
        'points_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('cantidad', sa.Integer(), nullable=True),
        sa.Column('motivo', sa.String(), nullable=True),
        sa.Column('fecha', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # PROMOTIONS (tipo_canje/valor_descuento los agrega a1b2c3d4e5f6;
    # direccion/latitude/longitude las agrega ce7d1e2f3a5b)
    op.create_table(
        'promotions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=True),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('costo_puntos', sa.Integer(), nullable=True),
        sa.Column('icono', sa.String(), nullable=True),
        sa.Column('categoria', sa.String(), nullable=True),
        sa.Column('activa', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # COUPONS
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=True),
        sa.Column('descuento_porcentaje', sa.Integer(), nullable=True),
        sa.Column('fecha_expiracion', sa.String(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_coupons_codigo', 'coupons', ['codigo'], unique=True)

    # RESERVATIONS (ix_reservations_* los crea 49a240f0fc25;
    # metodo_pago/tipo_vehiculo/origen agregadas por d3b7/a4c8/b5c9)
    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('patente', sa.String(), nullable=True),
        sa.Column('fecha_inicio', sa.String(), nullable=True),
        sa.Column('fecha_fin', sa.String(), nullable=True),
        sa.Column('dias_semana', sa.String(), nullable=True),
        sa.Column('monto_total', sa.Float(), nullable=True),
        sa.Column('monto_reembolsado', sa.Float(), nullable=True),
        sa.Column('fecha_pago', sa.String(), nullable=True),
        sa.Column('mp_preference_id', sa.String(), nullable=True),
        sa.Column('estado_pago', sa.String(), nullable=True),
        sa.Column('estado_reserva', sa.String(), nullable=True),
        sa.Column('sucursal_nombre', sa.String(), nullable=True),
        sa.Column('sucursal_info', sa.String(), nullable=True),
        sa.Column('tipo_estadia', sa.String(), nullable=True),
        sa.Column('cliente_nombre', sa.String(), nullable=True),
        sa.Column('recordatorio_confirmado', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # PARKING AFORO (columnas de reservas las agrega e6f7a8b9c0d1)
    op.create_table(
        'parking_aforo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capacidad_total', sa.Integer(), nullable=True),
        sa.Column('ocupacion_actual', sa.Integer(), nullable=True),
        sa.Column('capacidad_motos', sa.Integer(), nullable=True),
        sa.Column('ocupacion_motos', sa.Integer(), nullable=True),
        sa.Column('capacidad_camionetas', sa.Integer(), nullable=True),
        sa.Column('ocupacion_camionetas', sa.Integer(), nullable=True),
        sa.Column('ultima_actualizacion', sa.String(), nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sucursal'),
    )

    # SETTINGS
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clave', sa.String(), nullable=True),
        sa.Column('valor', sa.Float(), nullable=True),
        sa.Column('valor_str', sa.String(), nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # PARKING BRANCHES
    op.create_table(
        'parking_branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=True),
        sa.Column('direccion', sa.String(), nullable=True),
        sa.Column('telefono', sa.String(), nullable=True),
        sa.Column('horario', sa.String(), nullable=True),
        sa.Column('is_24h', sa.Boolean(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_parking_branches_nombre', 'parking_branches', ['nombre'], unique=True)

    # PARKING CAMERAS
    op.create_table(
        'parking_cameras',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # PARKING FLOORS (columnas de reservas las agrega e6f7a8b9c0d1)
    op.create_table(
        'parking_floors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), sa.ForeignKey('parking_branches.id'), nullable=True),
        sa.Column('nombre', sa.String(), nullable=True),
        sa.Column('capacidad_total', sa.Integer(), nullable=True),
        sa.Column('ocupacion_actual', sa.Integer(), nullable=True),
        sa.Column('capacidad_motos', sa.Integer(), nullable=True),
        sa.Column('ocupacion_motos', sa.Integer(), nullable=True),
        sa.Column('capacidad_camionetas', sa.Integer(), nullable=True),
        sa.Column('ocupacion_camionetas', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ACCESS LOGS (ocr_time la agrega f1a2b3c4d5e6 y backend_time se agrega y
    # se descarta en la misma cadena; ix_access_logs_sucursal/tipo_evento los
    # crea 49a240f0fc25)
    op.create_table(
        'access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patente_detectada', sa.String(), nullable=True),
        sa.Column('normalized_patente', sa.String(), nullable=True),
        sa.Column('tipo_evento', sa.String(), nullable=True),
        sa.Column('tipo_vehiculo', sa.String(), nullable=True),
        sa.Column('reserva_id', sa.Integer(), sa.ForeignKey('reservations.id'), nullable=True),
        sa.Column('floor_id', sa.Integer(), sa.ForeignKey('parking_floors.id'), nullable=True),
        sa.Column('fecha_hora', sa.String(), nullable=True),
        sa.Column('fecha_pago', sa.String(), nullable=True),
        sa.Column('imagen_path', sa.String(), nullable=True),
        sa.Column('pago_confirmado', sa.Boolean(), nullable=True),
        sa.Column('metodo_pago', sa.String(), nullable=True),
        sa.Column('costo_estadia', sa.Float(), nullable=True),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_access_logs_normalized_patente', 'access_logs', ['normalized_patente'], unique=False)

    # SUPPORT TICKETS (user_response la agrega d4f7c8e2a190)
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('categoria', sa.String(), nullable=False),
        sa.Column('sucursal', sa.String(), nullable=True),
        sa.Column('asunto', sa.String(), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('estado', sa.String(), nullable=True),
        sa.Column('respuesta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'], unique=False)
    op.create_index('ix_support_tickets_sucursal', 'support_tickets', ['sucursal'], unique=False)
    op.create_index('ix_support_tickets_estado', 'support_tickets', ['estado'], unique=False)

    # USER NOTIFICATIONS (ticket_id lo agrega d4f7c8e2a190)
    op.create_table(
        'user_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('mensaje', sa.String(), nullable=False),
        sa.Column('leido', sa.Boolean(), nullable=True),
        sa.Column('reserva_id', sa.Integer(), sa.ForeignKey('reservations.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_notifications_user_id', 'user_notifications', ['user_id'], unique=False)


def downgrade() -> None:
    """Revierte el esquema base."""
    op.drop_index('ix_user_notifications_user_id', table_name='user_notifications')
    op.drop_table('user_notifications')
    op.drop_index('ix_support_tickets_estado', table_name='support_tickets')
    op.drop_index('ix_support_tickets_sucursal', table_name='support_tickets')
    op.drop_index('ix_support_tickets_user_id', table_name='support_tickets')
    op.drop_table('support_tickets')
    op.drop_index('ix_access_logs_normalized_patente', table_name='access_logs')
    op.drop_table('access_logs')
    op.drop_table('parking_floors')
    op.drop_table('parking_cameras')
    op.drop_index('ix_parking_branches_nombre', table_name='parking_branches')
    op.drop_table('parking_branches')
    op.drop_table('settings')
    op.drop_table('parking_aforo')
    op.drop_table('reservations')
    op.drop_index('ix_coupons_codigo', table_name='coupons')
    op.drop_table('coupons')
    op.drop_table('promotions')
    op.drop_table('points_log')
    op.drop_index('ix_vehicles_patente', table_name='vehicles')
    op.drop_table('vehicles')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_dni', table_name='users')
    op.drop_table('users')