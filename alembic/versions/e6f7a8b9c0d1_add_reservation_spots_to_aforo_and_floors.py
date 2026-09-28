"""add_reservation_spots_to_aforo_and_floors

Revision ID: e6f7a8b9c0d1
Revises: 49a240f0fc25
Create Date: 2026-09-05 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = '49a240f0fc25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('parking_aforo', schema=None) as batch_op:
        batch_op.add_column(sa.Column('capacidad_reservas_autos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_autos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas_motos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_motos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas_camionetas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_camionetas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas', sa.Integer(), nullable=True))

    with op.batch_alter_table('parking_floors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('capacidad_reservas_autos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_autos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas_motos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_motos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas_camionetas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas_camionetas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('capacidad_reservas', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocupacion_reservas', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('parking_floors', schema=None) as batch_op:
        batch_op.drop_column('ocupacion_reservas')
        batch_op.drop_column('capacidad_reservas')
        batch_op.drop_column('ocupacion_reservas_camionetas')
        batch_op.drop_column('capacidad_reservas_camionetas')
        batch_op.drop_column('ocupacion_reservas_motos')
        batch_op.drop_column('capacidad_reservas_motos')
        batch_op.drop_column('ocupacion_reservas_autos')
        batch_op.drop_column('capacidad_reservas_autos')

    with op.batch_alter_table('parking_aforo', schema=None) as batch_op:
        batch_op.drop_column('ocupacion_reservas')
        batch_op.drop_column('capacidad_reservas')
        batch_op.drop_column('ocupacion_reservas_camionetas')
        batch_op.drop_column('capacidad_reservas_camionetas')
        batch_op.drop_column('ocupacion_reservas_motos')
        batch_op.drop_column('capacidad_reservas_motos')
        batch_op.drop_column('ocupacion_reservas_autos')
        batch_op.drop_column('capacidad_reservas_autos')
