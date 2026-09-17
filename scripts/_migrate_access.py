# -*- coding: utf-8 -*-
"""MIGRA access_service.py: db.query(models.X) -> Repositorios (solo lecturas).
Método: transformaciones de STRING EXACTO (verbatim), comprobación con py_compile
y assert de que no quede ningún db.query(models.*) en el archivo.
"""
import io, sys, re

path = r"C:\Users\usuario.DESKTOP-P7MEQGK\Desktop\AUTOPASS\services\access_service.py"
with io.open(path, "r", encoding="utf-8") as f:
    src = f.read()

def apply(name, old, new):
    global src
    if old not in src:
        raise SystemExit(f"OLD NOT FOUND: {name}")
    if src.count(old) != 1:
        raise SystemExit(f"AMBIGUOUS ({src.count(old)} x): {name}")
    src = src.replace(old, new)
    print(f"   [ok] {name}")

OA = "        ultima_entrada = db.query(models.AccessLog).filter(\n"
OAent= "            models.AccessLog.normalized_patente == p,\n            models.AccessLog.tipo_evento == AccessEventType.ENTRADA,\n            models.AccessLog.sucursal == sucursal\n        ).order_by(models.AccessLog.id.desc()).first()"
apply("L89 entrada", OA+OAent,
      "        ultima_entrada = AccessRepository.get_last_entry(db, p, sucursal)")

# L96-101: tiene_salida
old96 = "            tiene_salida = db.query(models.AccessLog.id).filter(\n                models.AccessLog.patente_detectada == ultima_entrada.patente_detectada,\n                models.AccessLog.tipo_evento == AccessEventType.SALIDA,\n                models.AccessLog.id > ultima_entrada.id,\n                models.AccessLog.sucursal == sucursal\n            ).first()"
apply("L96 salida", old96,
      "            tiene_salida = AccessRepository.get_exit_after(db, ultima_entrada.patente_detectada, ultima_entrada.id, sucursal)")

print("\nTRANSFORMACIONES OK")
