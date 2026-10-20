"""reservas: constraint de no-solape de patente por sede (solo Postgres)

FASE 4 del plan de Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md.

Red de seguridad de ultimo nivel contra R2 (dos reservas vigentes de la misma
patente solapadas en la misma sede). El lock `patente:` de la Fase 2 ya lo evita a
nivel de aplicacion; este constraint lo evita a nivel de MOTOR, asi que tambien
cubre cualquier alta que esquive el servicio (scripts, seeds, SQL a mano).

Como funciona: un `EXCLUDE USING gist` que declara "no pueden coexistir dos filas
iguales en (patente normalizada, sede) cuyos rangos de fecha se superpongan".

Decisiones de diseno (importante, se apartan del borrador del informe):

- SIN columna `patente_norm`: el informe proponia agregar y mantener una columna
  normalizada. Se usa directo la EXPRESION `upper(replace(patente,' ',''))`, que es
  exactamente lo que evalua `get_overlap_by_patente` en el repositorio. Asi no hay
  columna nueva, ni backfill, ni un write-path que mantener sincronizado (si
  alguien insertaba sin setearla, el constraint no protegia).
- Sobre `sucursal_id`, NO `sucursal_nombre`: el nombre de la sede no es una columna
  (vive en `parking_branches` y se resuelve por un hybrid). La columna real es
  `sucursal_id`.
- Los estados usan los valores REALES del enum (`'Pendiente'`, `'Activa'`,
  `'Pagado'`, capitalizados). El borrador del informe usaba mayusculas, que no
  matchean ninguna fila y habrian creado un constraint inutil.
- Rango `[)`: `tsrange(fecha_inicio, fecha_fin, '[)')` reproduce la semantica del
  repositorio (`inicio < hasta AND fin > desde`), asi que dos reservas contiguas
  (una termina cuando empieza la otra) NO chocan.
- El predicado parcial solo mira reservas vigentes y con fechas cargadas: las
  CANCELADAS/COMPLETADAS y las que no tienen fecha no bloquean nada.

Alcance: SOLO Postgres. En SQLite (dev/tests) el constraint no existe y el guard de
aplicacion de la Fase 2 queda como unica defensa. El modelo NO declara el constraint
porque `create_all` en SQLite falla al intentar emitir un `EXCLUDE` (romperia la
suite entera); por eso vive unicamente aca, en la migracion.

Es idempotente: chequea por catalogo si la extension/constraint ya estan antes de
crear nada (sync_schema corre create_all antes que Alembic).

Revision ID: b1c2d3e4f5a6
Revises: e5f6a7b8c9d0
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = "reservations"
CONSTRAINT = "ex_reservations_solape_patente"

# Normalizacion de patente: MISMA expresion que usa
# `ReservationRepository.get_overlap_by_patente` (mayusculas, sin espacios).
EXPR_PATENTE = "upper(replace(patente, ' ', ''))"

# Predicado parcial: solo reservas vigentes y con fechas.
WHERE_VIGENTES = (
    "estado_reserva IN ('Pendiente','Activa') "
    "AND estado_pago IN ('Pendiente','Pagado') "
    "AND fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL"
)

# DDL completo del constraint (fuente unica: la migracion y el test lo comparten).
DDL_CONSTRAINT = (
    f"ALTER TABLE {TABLA} ADD CONSTRAINT {CONSTRAINT} "
    f"EXCLUDE USING gist ("
    f"({EXPR_PATENTE}) WITH =, "
    f"(sucursal_id) WITH =, "
    f"tsrange(fecha_inicio, fecha_fin, '[)') WITH &&"
    f") WHERE ({WHERE_VIGENTES})"
)


def _es_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _constraint_existe() -> bool:
    bind = op.get_bind()
    r = bind.execute(sa.text(
        "SELECT 1 FROM pg_constraint WHERE conname = :n AND conrelid = to_regclass(:t)"
    ), {"n": CONSTRAINT, "t": TABLA}).scalar()
    return bool(r)


def upgrade() -> None:
    """Crea el EXCLUDE de no-solape de patente por sede (solo Postgres)."""
    if not _es_postgres():
        # SQLite no soporta EXCLUDE: el guard de la Fase 2 sigue siendo la defensa.
        return
    # btree_gist aporta el operador `=` por igualdad en tipos escalares (text, int)
    # dentro de un indice gist; sin la extension el EXCLUDE no compila.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    if not _constraint_existe():
        op.execute(DDL_CONSTRAINT)


def downgrade() -> None:
    """Elimina el constraint (no borra btree_gist: puede usarla otra cosa)."""
    if not _es_postgres():
        return
    if _constraint_existe():
        op.execute(f"ALTER TABLE {TABLA} DROP CONSTRAINT {CONSTRAINT}")
