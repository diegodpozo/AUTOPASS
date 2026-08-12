"""Migra los datos de la base Turso/libSQL (origen) a Postgres (destino, ej: Neon/Supabase).

Uso:
    venv\\Scripts\\python.exe scripts\\migrate_turso_to_neon.py --to-url "postgresql://usuario:pass@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require"

El origen se toma del DATABASE_URL del .env actual (Turso). Se preservan los IDs y se
sincronizan las secuencias para que los nuevos inserts no colisionen.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.config import settings
from sqlalchemy.pool import QueuePool
import models

# Orden respetando claves foraneas
TABLES = [
    models.User,
    models.ParkingBranch,
    models.Vehicle,
    models.ParkingFloor,
    models.ParkingAforo,
    models.Settings,
    models.Promotion,
    models.Coupon,
    models.Reservation,
    models.AccessLog,
    models.PointsLog,
    models.UserNotification,
    models.SupportTicket,
]


def make_engine(url: str):
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    if url.startswith(("libsql://", "sqlite+libsql://")):
        if not url.startswith("sqlite+"):
            url = "sqlite+" + url
        return create_engine(url, connect_args={"auth_token": settings.TURSO_AUTH_TOKEN}, poolclass=QueuePool)
    return create_engine(url)


def main():
    parser = argparse.ArgumentParser(description="Migra Turso/libSQL -> Postgres preservando IDs.")
    parser.add_argument("--to-url", required=True, help="URL Postgres destino (Neon/Supabase)")
    parser.add_argument("--from-url", default=None, help="URL Turso origen (default: DATABASE_URL del .env)")
    args = parser.parse_args()

    from_url = args.from_url or settings.DATABASE_URL
    src = make_engine(from_url)
    dst = make_engine(args.to_url)

    print(f"Origen : {from_url.split('?')[0]}")
    print(f"Destino: {args.to_url.split('?')[0]}")

    models.Base.metadata.create_all(bind=dst)
    print("Schema creado en destino.")

    with src.connect() as s, dst.begin() as d:
        for cls in TABLES:
            rows = [dict(r._mapping) for r in s.execute(cls.__table__.select())]
            if not rows:
                print(f"- {cls.__tablename__}: 0 filas")
                continue
            d.execute(cls.__table__.insert(), rows)
            print(f"- {cls.__tablename__}: {len(rows)} filas")

        for cls in TABLES:
            tbl = cls.__tablename__
            d.execute(
                text(f"SELECT setval(pg_get_serial_sequence(:tbl, 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1))"),
                {"tbl": tbl},
            )

    print("DONE. Secuencias sincronizadas.")


if __name__ == "__main__":
    main()
