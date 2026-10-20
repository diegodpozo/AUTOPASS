"""Utilidades compartidas para los tests que necesitan un Postgres real.

Varios tests del plan de concurrencia necesitan Postgres y NO pueden correr en
SQLite (el lock `pg_advisory_xact_lock` es no-op, y el `EXCLUDE` de la Fase 4 no
existe en SQLite). Para no duplicar el mismo andamiaje en cada archivo, aca vive:

- `POSTGRES_URL`: la URL del `.env` normalizada a psycopg 3, o None.
- `pg_only`: marcador de skip cuando no hay Postgres configurado.
- `solo_si_postgres_esta_vivo()`: salta el test si la base no responde (sin red).
- `crear_schema_efimero()`: crea un schema propio y devuelve (engine, admin, schema).
  TODA la conexion usa `search_path=<schema>`, asi que nada toca las tablas reales.
- `borrar_schema_efimero(admin, schema)`: lo elimina al terminar.

Es la base comun de `test_concurrencia_reservas.py` (R1/R2) y
`test_concurrencia_constraints_postgres.py` (Fase 4).
"""
import importlib.util
import os
import pathlib
import uuid

import pytest
from sqlalchemy import create_engine, text

from core.config import settings

RAIZ_REPO = pathlib.Path(__file__).resolve().parent.parent


def cargar_migracion(prefijo_revision: str):
    """Carga una migracion de Alembic por el prefijo de su revision.

    `alembic/versions` no es un paquete importable, asi que se carga por ruta
    (igual que lo hace Alembic). Sirve para que un test use el DDL REAL de la
    migracion en vez de copiarlo.
    """
    coincidencias = sorted((RAIZ_REPO / "alembic" / "versions").glob(f"{prefijo_revision}*.py"))
    if not coincidencias:
        raise FileNotFoundError(f"No hay migracion que empiece con {prefijo_revision!r}")
    archivo = coincidencias[-1]
    spec = importlib.util.spec_from_file_location(f"_mig_{prefijo_revision}", archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _resolver_url() -> str | None:
    """URL de Postgres normalizada a psycopg 3, o None si no hay Postgres."""
    url = settings.DATABASE_URL
    if not url or not url.startswith("postgresql"):
        return None
    if "+" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url if url.startswith("postgresql+psycopg://") else None


POSTGRES_URL = _resolver_url()

# Con REQUIRE_POSTGRES=1 (lo usa el CI) un Postgres ausente NO es un skip: es un fallo.
# De lo contrario el paso de CI daria verde con el grupo entero salteado, o sea los tests
# de concurrencia no habrian corrido y nadie se enteraria.
_REQUIERE_POSTGRES = os.getenv("REQUIRE_POSTGRES") == "1"

pg_only = pytest.mark.skipif(
    POSTGRES_URL is None and not _REQUIERE_POSTGRES,
    reason="Requiere Postgres real (el lock advisory y el EXCLUDE no existen en SQLite).",
)


def postgres_responde(url: str = None) -> bool:
    """True si la base responde (evita fallar la suite sin red)."""
    url = url or POSTGRES_URL
    if not url:
        return False
    try:
        eng = create_engine(url, connect_args={"connect_timeout": 8})
        with eng.connect() as c:
            c.execute(text("select 1"))
        eng.dispose()
        return True
    except Exception:
        return False


def solo_si_postgres_esta_vivo() -> None:
    """Salta el test si no hay Postgres configurado o no responde.

    Con `REQUIRE_POSTGRES=1` (que usa el CI) NO se salta: falla. Sin eso, un servicio
    de Postgres caido en CI daria la suite en VERDE con todo el grupo salteado, o sea
    los tests de concurrencia no habrian corrido y nadie se enteraria.
    """
    requerido = os.getenv("REQUIRE_POSTGRES") == "1"
    url = _resolver_url()  # se re-resuelve ahora, no confia en el valor de import
    if url is None:
        if requerido:
            pytest.fail(
                "REQUIRE_POSTGRES=1 pero DATABASE_URL no es Postgres "
                f"(valor actual: {settings.DATABASE_URL!r})"
            )
        pytest.skip("Sin DATABASE_URL de Postgres")
    if not postgres_responde(url):
        if requerido:
            pytest.fail(f"REQUIRE_POSTGRES=1 pero Postgres no responde ({url})")
        pytest.skip("Postgres no responde (¿sin red?)")


def crear_schema_efimero(prefijo: str = "rk_test"):
    """Crea un schema aislado y devuelve (engine, admin_engine, schema).

    El engine devuelto fija `search_path` a ese schema, asi que tanto `create_all`
    como las queries del test viven ahi y no tocan las tablas reales.
    """
    schema = f"{prefijo}_{uuid.uuid4().hex[:12]}"
    admin = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 10})
    with admin.begin() as c:
        c.execute(text(f'CREATE SCHEMA "{schema}"'))
    eng = create_engine(
        POSTGRES_URL,
        connect_args={"connect_timeout": 10, "options": f"-csearch_path={schema}"},
    )
    return eng, admin, schema


def borrar_schema_efimero(admin, schema: str) -> None:
    """Elimina el schema efimero y libera el engine admin."""
    try:
        with admin.begin() as c:
            c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    finally:
        admin.dispose()
