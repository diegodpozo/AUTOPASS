"""add orden column to parking_cameras

Permite ordenar manualmente las cámaras en la grilla de monitoreo. Las cámaras
existentes conservan su orden actual (por id). Un valor NULL significa "sin
ordenar" y se ubica al final de la grilla.

Revision ID: b8f1c2d3e4a5
Revises: f9a8b7c6d5e4
Create Date: 2026-10-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b8f1c2d3e4a5'
down_revision: Union[str, Sequence[str], None] = 'f9a8b7c6d5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('parking_cameras', schema=None) as batch_op:
        batch_op.add_column(sa.Column('orden', sa.Integer(), nullable=True))
    # Preservar el orden actual (por id) en las cámaras ya existentes.
    op.execute("UPDATE parking_cameras SET orden = id WHERE orden IS NULL")


def downgrade() -> None:
    with op.batch_alter_table('parking_cameras', schema=None) as batch_op:
        batch_op.drop_column('orden')
