"""add_access_logs_covering_indexes

Revision ID: cdb7d130c856
Revises: ce7d1e2f3a5b
Create Date: 2026-09-27 21:25:03.843756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdb7d130c856'
down_revision: Union[str, Sequence[str], None] = 'ce7d1e2f3a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Indice compuesto para subqueries correlacionadas sobre access_logs:
    # - unpaid_entries_without_exit (NOT EXISTS patente_detectada+tipo_evento+sucursal+fecha_hora)
    # Evita el full-scan por fila que degradaba /v1/reports/financial-summary (rutas A5, 2026-09-27).
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.create_index(
            'ix_access_logs_pat_tipo_suc_fecha',
            ['patente_detectada', 'tipo_evento', 'sucursal', 'fecha_hora'],
            unique=False,
        )
        # Indice para get_entry_for_reserva (N+1 del cleanup de reservas vencidas
        # en GET /v1/admin/reservations): filtra por reserva_id + tipo_evento.
        batch_op.create_index(
            'ix_access_logs_reserva_id',
            ['reserva_id', 'tipo_evento'],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.drop_index('ix_access_logs_reserva_id')
        batch_op.drop_index('ix_access_logs_pat_tipo_suc_fecha')
