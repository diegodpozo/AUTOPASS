"""mercadopago: payment_id unico (clave de idempotencia de webhooks)

FASE 5 del plan de Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md.

Mercado Pago reintenta los webhooks, asi que el mismo pago puede llegar mas de
una vez. `payment_id` (el id del pago en MP) pasa a ser UNICO: un segundo intento
de aplicar el mismo pago choca contra el indice en vez de acreditar dos veces.

Detalle importante sobre los vacios: los pagos que todavia no tienen id de MP se
guardan como NULL (el servicio ya no escribe ''). Varios NULL NO colisionan en un
indice unico, asi que los pendientes conviven. Antes de crear el indice se
normalizan a NULL los '' que hayan quedado de versiones previas, para no chocar
entre si.

Es idempotente: `sync_schema` corre `create_all` antes que Alembic, y en una base
nueva el indice ya puede existir. Se chequea por inspector antes de crear/borrar.

Revision ID: e5f6a7b8c9d0
Revises: d9e0f1a2b3c4
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd9e0f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLA = 'mercadopago_payments'
_INDICE = 'ix_mercadopago_payments_payment_id'
_COLUMNA = 'payment_id'


def _tiene_indice(nombre: str) -> bool:
    """True si el indice ya existe (evita chocar con lo creado por create_all)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(i['name'] == nombre for i in inspector.get_indexes(_TABLA))


def upgrade() -> None:
    """Normaliza '' -> NULL y crea el indice unico de payment_id."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columnas = {c['name'] for c in inspector.get_columns(_TABLA)}
    if _COLUMNA not in columnas:
        # La tabla ni siquiera existe todavia: la creara create_all con el indice.
        return

    # Los '' de versiones previas pasan a NULL para no colisionar entre si.
    bind.execute(sa.text(f"UPDATE {_TABLA} SET {_COLUMNA} = NULL WHERE {_COLUMNA} = ''"))

    if not _tiene_indice(_INDICE):
        op.create_index(_INDICE, _TABLA, [_COLUMNA], unique=True)


def downgrade() -> None:
    """Elimina el indice unico de payment_id (la columna queda igual)."""
    if _tiene_indice(_INDICE):
        op.drop_index(_INDICE, table_name=_TABLA)
