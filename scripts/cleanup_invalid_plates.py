"""Elimina de todas las tablas los registros cuya patente NO coincide con un
formato LATAM reconocido (ver core.normalize.is_valid_plate).

Revisa:
    - access_logs.patente_detectada / normalized_patente
    - reservations.patente
    - vehicles.patente
    - users.patente
    - mercadopago_payments.patente

Idempotente: una segunda corrida no encuentra nada que borrar.
Antes de borrar guarda un respaldo JSON de las filas afectadas.

Uso:
    python scripts/cleanup_invalid_plates.py --dry-run   # solo muestra que se borraria
    python scripts/cleanup_invalid_plates.py             # borra y respalda
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.database import SessionLocal
from core.normalize import normalize_plate, is_valid_plate
from models import AccessLog, User, Vehicle
from models.mercadopago import MercadoPagoPayment
from models.reservation import Reservation

BACKUP_DEFAULT = os.path.join(ROOT, "data", "pruebas", "cleanup_invalid_plates_backup.json")


def _bad(patente) -> bool:
    """TRUE SI LA PATENTE NO ESTA VACIA Y NO TIENE UN FORMATO RECONOCIDO."""
    clean = normalize_plate(patente or "")
    return bool(clean) and not is_valid_plate(clean)


def _targets():
    return [
        ("access_logs", AccessLog,
         lambda r: _bad(r.patente_detectada) or _bad(r.normalized_patente)),
        ("reservations", Reservation, lambda r: _bad(r.patente)),
        ("vehicles", Vehicle, lambda r: _bad(r.patente)),
        ("users", User, lambda r: _bad(r.patente)),
        ("mercadopago_payments", MercadoPagoPayment, lambda r: _bad(r.patente)),
    ]


def _row_snapshot(table, r) -> dict:
    data = {}
    for col in r.__table__.columns.keys():
        val = getattr(r, col, None)
        data[col] = val if isinstance(val, (int, float, str, type(None))) else str(val)
    data["_table"] = table
    return data


def main():
    ap = argparse.ArgumentParser(description="Borra patentes con formato invalido en todas las tablas")
    ap.add_argument("--dry-run", action="store_true", help="Solo muestra lo que se borraria, sin tocar la BD")
    ap.add_argument("--backup", default=BACKUP_DEFAULT, help="Ruta del respaldo JSON de filas borradas")
    args = ap.parse_args()

    db = SessionLocal()
    total = 0
    respaldo = []
    try:
        for table, model, es_invalida in _targets():
            filas = db.query(model).all()
            malas = [r for r in filas if es_invalida(r)]
            for r in malas:
                respaldo.append(_row_snapshot(table, r))
                if not args.dry_run:
                    db.delete(r)
            total += len(malas)
            print(f"{table}: {len(malas)} invalidas ({len(filas)} totales)")

        if args.dry_run:
            print(f"\nDRY-RUN: se eliminarian {total} filas. Nada fue modificado.")
            return

        if total:
            os.makedirs(os.path.dirname(args.backup), exist_ok=True)
            with open(args.backup, "w", encoding="utf-8") as fh:
                json.dump(respaldo, fh, ensure_ascii=False, indent=2)
            print(f"\nRespaldo guardado en: {args.backup}")

        db.commit()
        print(f"TOTAL eliminadas: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
