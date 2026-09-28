"""drop redundant pk id indexes

Revision ID: 8b3e9e815c78
Revises: cdb7d130c856
Create Date: 2026-09-27 21:42:48.142095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b3e9e815c78'
down_revision: Union[str, Sequence[str], None] = 'cdb7d130c856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Los modelos declaran id sin `index=True` (la PK ya indexa): se alinea
    # la cadena Alembic eliminando los dos indices redundantes sobre el PK
    # id que si se habian creado en la cadena (49a240f0fc25).
    with op.batch_alter_table('redemption_tickets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_redemption_tickets_id'))

    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_id'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_id'), ['id'], unique=False)

    with op.batch_alter_table('redemption_tickets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_redemption_tickets_id'), ['id'], unique=False)