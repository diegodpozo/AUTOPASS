"""BLOQUEO TRANSACCIONAL UNICO (FASE 2 - AUDITORIA DE CONCURRENCIA DE RESERVAS).

Serializa las secciones criticas del negocio (crear/modificar reserva, pagar,
cancelar, transiciones del worker) para eliminar las carreras tipo
check-then-act descritas en Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md.

Diseno (no repetir logica de bloqueo en servicios/rutas: usar SIEMPRE este helper):

- PostgreSQL (produccion/Neon): usa ``pg_advisory_xact_lock``, que es un lock
  A NIVEL DE TRANSACCION: se libera solo en commit/rollback, por lo que es
  seguro con el transaction pooling del pooler de Neon (los locks a nivel de
  SESESSION si se filtran ahi; los transaccionales no).
- SQLite (dev/tests): no-op documentado, porque SQLite no tiene advisory locks.
  Los tests secuenciales existentes no cambian de comportamiento.
- Timeout: ``SET LOCAL lock_timeout`` solo alrededor de la adquisicion; si no
  se consigue el lock a tiempo se lanza ``LockTimeoutError``, que main.py
  traduce a HTTP 409 ("reintenta") sin dejar la transaccion colgada.
- Orden de adquisicion: las claves se adquieren SIEMPRE ordenadas
  alfabeticamente para que dos secciones criticas con claves en comun no
  puedan entrar en deadlock mutuo.
"""

import contextlib
import threading

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from core.config import settings
from core.logger import get_logger

logger = get_logger("DbLock")

# SQLSTATE 55P03 = lock_not_available: es el que Postgres lanza cuando vence
# lock_timeout. (OJO: 57014/query_canceled es el de statement_timeout; NO sirve
# aqui.) Se chequea por codigo para no depender de la clase concreta de psycopg
# ni congelar el import en SQLite.
_SQLSTATE_LOCK_TIMEOUT = "55P03"


class LockTimeoutError(Exception):
    """El lock transaccional no se pudo obtener dentro de LOCK_TIMEOUT_SECONDS."""


# Aviso de no-soporte una sola vez por proceso (para no spamear el log en dev).
_lock_no_soportado_advertido = threading.Event()


def _fue_timeout_de_lock(exc: OperationalError) -> bool:
    """Detecta si un OperationalError de SQLAlchemy viene del lock_timeout de Postgres."""
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    return sqlstate == _SQLSTATE_LOCK_TIMEOUT


def clave_aforo(sucursal_nombre: str, tipo_vehiculo) -> str:
    """Clave canonica R1: capacidad de reservas de un tipo de vehiculo en una sede."""
    tipo = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo or "Auto")
    return f"aforo:{sucursal_nombre}:{tipo}"


def clave_patente(patente_norm: str, sucursal_nombre: str) -> str:
    """Clave canonica R2: solapamiento de una misma patente dentro de una sede."""
    return f"patente:{patente_norm}:{sucursal_nombre}"


def clave_usuario(user_id) -> str:
    """Clave canonica R3: saldo y puntos de un usuario (operaciones sobre su cuenta)."""
    return f"usuario:{user_id}" if user_id is not None else ""


def clave_reserva(res_id) -> str:
    """Clave canonica R3/R5: transiciones de estado de una reserva concreta."""
    return f"reserva:{res_id}" if res_id is not None else ""


def refrescar(db: Session, *objetos) -> None:
    """Regla critica (informe Fase 2): relee bajo el lock los objetos que se van a
    decidir/mutar, porque el caller pudo haberlos cargado ANTES de adquirir el lock.

    Solo refresca instancias que pertenecen a esta sesion (los de otra sesion o los
    transitorios se ignoran, para no romper callers exoticos ni tests). Ojo: un
    refresh descarta cambios sin flush sobre ese objeto; por eso en la practica
    solo se refrescan objetos recien cargados o limpios (current_user, etc.).
    """
    for obj in objetos:
        if obj is not None and obj in db:
            db.refresh(obj)


@contextlib.contextmanager
def bloqueo_transaccional(db: Session, *claves: str):
    """Serializa una seccion critica que abarca lecturas y escrituras de decision.

    Uso::

        with bloqueo_transaccional(db, clave_aforo(sucursal, tipo)):
            disp = verificar_disponibilidad(...)
            if not disp["disponible"]:
                raise HTTPException(...)
            db.add(...); db.commit()

    Contrato:

    - Las claves se adquieren ordenadas alfabeticamente (anti-deadlock).
    - El lock vive hasta el fin de la transaccion (commit/rollback); no hay que
      liberarlo a mano ni se puede liberar antes a proposito.
    - Dentro del ``with`` hay que (re)ejecutar las validaciones de decision;
      NO se debe reusar un valor leido ANTES de entrar.
    - Claves vacias (ej. usuario sin id) se ignoran; sin claves validas el
      bloque es no-op.
    """
    claves_ordenadas = sorted(set(k for k in claves if k))
    if not claves_ordenadas:
        yield
        return

    dialect = db.get_bind().dialect.name
    if dialect != "postgresql":
        if not _lock_no_soportado_advertido.is_set():
            _lock_no_soportado_advertido.set()
            logger.debug(
                "DBLock: dialecto %s sin advisory locks; las secciones criticas quedan "
                "sin serializar (solo afecta a SQLite de desarrollo/tests).", dialect
            )
        yield
        return

    timeout_ms = max(1, int(settings.LOCK_TIMEOUT_SECONDS * 1000))
    # SET LOCAL solo aplica a la transaccion actual y no sobrevive al commit.
    db.execute(text(f"SET LOCAL lock_timeout = '{timeout_ms}ms'"))
    try:
        for clave in claves_ordenadas:
            # hashtextextended convierte la clave canonica en un bigint estable
            # dentro del propio Postgres (sin replicar el hash en Python).
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:clave, 0))"),
                {"clave": clave},
            )
    except OperationalError as exc:
        if _fue_timeout_de_lock(exc):
            raise LockTimeoutError(
                f"No se pudo adquirir el bloqueo de {claves_ordenadas} en "
                f"{settings.LOCK_TIMEOUT_SECONDS}s."
            ) from exc
        raise
    # Lock ya adquirido: restaurar el timeout default para que las queries
    # restantes de la seccion no queden acotadas por el timeout del lock.
    db.execute(text("SET LOCAL lock_timeout = DEFAULT"))
    try:
        yield
    finally:
        # Si la seccion critica termino con excepcion, el rollback de la sesión
        # (get_db/SessionLocal) libera los locks; aqui no hay nada que hacer.
        pass
