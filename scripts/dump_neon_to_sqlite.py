"""Volcado Neon (Postgres) -> SQLite local.

- Solo LEE de Neon (nunca escribe ni modifica).
- Crea el esquema SQLite desde los modelos (init sobre el engine SQLite).
- Copia tabla por tabla en orden padres->hijos, preservando ids.
- Idempotente: si el archivo destino existe, se puede borrar y rehacer.

Uso:
    venv\\Scripts\\python.exe scripts\\dump_neon_to_sqlite.py [ruta_sqlite]
Default: C:\\xampp\\htdocs\\AUTOPASS\\data\\local_dev.db
"""
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.database import normalize_database_url


def neon_url() -> str:
    url = normalize_database_url(settings.DATABASE_URL)
    if not url.startswith("postgresql"):
        sys.exit(f"ERROR: .env DATABASE_URL no es Postgres/Neon: {url[:40]}...")
    return url


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "local_dev.db")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        print(f"Borrando destino previo: {dest}")
        os.remove(dest)

    pg = create_engine(neon_url(), pool_pre_ping=True, pool_recycle=1800)
    lite = create_engine(f"sqlite:///{dest.replace(os.sep, '/')}", connect_args={"check_same_thread": False})

    # 1) Esquema SQLite desde los modelos
    import models  # noqa: F401  (registra todas las tablas en Base.metadata)
    from core.database import Base
    Base.metadata.create_all(bind=lite)
    print("Schema SQLite creado desde modelos.")

    pg_insp = inspect(pg)
    pg_tables = set(pg_insp.get_table_names())
    lite_insp = inspect(lite)
    lite_tables = set(lite_insp.get_table_names())

    # 2) Orden padres->hijos segun FKs (topologico simple)
    fks = {t: set() for t in pg_tables}
    for t in pg_tables:
        for fk in pg_insp.get_foreign_keys(t):
            ref = fk.get("referred_table")
            if ref and ref != t and ref in pg_tables:
                fks[t].add(ref)
    order, seen = [], set()

    def visit(t):
        if t in seen:
            return
        seen.add(t)
        for r in fks.get(t, ()):
            visit(r)
        order.append(t)

    for t in pg_tables:
        visit(t)

    # 3) Copia fila por fila (preserva ids). Tablas no presentes en SQLite se omiten.
    pg_conn = pg.connect()
    lite_conn = lite.connect()
    lite_conn.execute(text("PRAGMA foreign_keys=OFF"))
    total = 0
    for t in order:
        if t not in lite_tables:
            print(f"  (omitida, no existe en SQLite): {t}")
            continue
        rows = pg_conn.execute(text(f'SELECT * FROM "{t}"')).mappings().all()
        if not rows:
            print(f"  {t:26s} 0 filas")
            continue
        lite_cols = {c["name"] for c in lite_insp.get_columns(t)}
        cols = [c for c in rows[0].keys() if c in lite_cols]
        params = [{c: r[c] for c in cols} for r in rows]
        ins = text(f'INSERT INTO "{t}" ({", ".join(chr(34)+c+chr(34) for c in cols)}) '
                   f'VALUES ({", ".join(":"+c for c in cols)})')
        lite_conn.execute(ins, params)
        lite_conn.commit()
        total += len(rows)
        print(f"  {t:26s} {len(rows):5d} filas")
    lite_conn.execute(text("PRAGMA foreign_keys=ON"))
    lite_conn.commit()
    lite_conn.close()
    pg_conn.close()
    print(f"\nOK. {total} filas copiadas a {dest}")

    # 4) Reset de secuencias para SQLite (AUTOINCREMENT se maneja solo; nada extra).
    size = os.path.getsize(dest)
    print(f"DB SQLite: {dest} ({size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
