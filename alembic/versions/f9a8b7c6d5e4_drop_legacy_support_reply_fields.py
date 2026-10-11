"""drop legacy respuesta/user_response from support_tickets

El hilo `support_ticket_messages` es la unica fuente de verdad de la
conversacion. Las columnas `respuesta` y `user_response` duplicaban el ultimo
mensaje de admin/usuario y ya no se escriben ni se exponen.

Revision ID: f9a8b7c6d5e4
Revises: b2f4e8c1a9d7
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f9a8b7c6d5e4'
down_revision: Union[str, Sequence[str], None] = 'b2f4e8c1a9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.drop_column('user_response')
        batch_op.drop_column('respuesta')


def downgrade() -> None:
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('respuesta', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('user_response', sa.Text(), nullable=True))
