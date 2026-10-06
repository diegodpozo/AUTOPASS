"""Genera movimientos DEMO (entradas/salidas ALPR) por sucursal con distribución realista
de tráfico (día de la semana x hora) para alimentar métricas y el mapa de calor de horarios.

Reejecutable: primero borra los movimientos que él mismo generó (imagen_path = MARCA),
así no duplica datos entre corridas.

Uso:
    python scripts/generate_demo_traffic.py [--dias 56] [--por-dia 20] [--seed 7]
"""

import argparse
import random
from datetime import datetime, timedelta

from core.database import SessionLocal
from models import AccessLog, ParkingBranch, Vehicle

MARCA = "demo:traffic"

# PESO RELATIVO DE TRAFICO POR DIA (0 = lunes .. 6 = domingo)
DIAS_PESO = {0: 1.0, 1: 1.05, 2: 1.0, 3: 1.0, 4: 1.1, 5: 0.75, 6: 0.6}

# PESO POR HORA (0..23): picos laborales 8h, 13h y 18-19h
HORAS_PESO = [0, 0, 0, 0, 0, 0, 1, 3, 7, 5, 4, 4, 6, 8, 5, 4, 5, 7, 10, 8, 5, 3, 2, 1]

# FACTOR POR SUCURSAL (volumen relativo); las no listadas usan 1.0
SUCURSAL_PESO = {
    "Castelar": 1.4,
    "Ituzaingó": 1.2,
    "Morón": 1.0,
    "Santos Dumont 686": 0.9,
    "Central": 1.1,
}

METODOS_PAGO = ["Efectivo", "Tarjeta", "MercadoPago", "QR"]
TIPOS_VEHICULO = ["Auto", "Moto", "Camioneta"]


def _elegir_hora(rng: random.Random) -> int:
    horas = list(range(24))
    return rng.choices(horas, weights=HORAS_PESO, k=1)[0]


def generar(db, dias: int, por_dia: int, seed: int) -> dict:
    rng = random.Random(seed)

    patentes = [
        (v.patente, v.tipo.value if hasattr(v.tipo, "value") else str(v.tipo))
        for v in db.query(Vehicle).all()
    ]
    if not patentes:
        return {"entradas": 0, "salidas": 0, "aviso": "sin vehiculos"}

    sucursales = [b.nombre for b in db.query(ParkingBranch).filter(ParkingBranch.activa.is_(True)).all()]

    # LIMPIA GENERACIONES ANTERIORES (idempotente)
    borrados = db.query(AccessLog).filter(AccessLog.imagen_path == MARCA).delete(synchronize_session=False)

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    entradas = salidas = 0

    for offset in range(dias, 0, -1):
        dia = hoy - timedelta(days=offset)
        factor_dia = DIAS_PESO[dia.weekday()]
        for sucursal in sucursales:
            factor_suc = SUCURSAL_PESO.get(sucursal, 1.0)
            n = max(1, round(rng.uniform(0.7, 1.3) * por_dia * factor_dia * factor_suc))
            for _ in range(n):
                patente, tipo = rng.choice(patentes)
                h = _elegir_hora(rng)
                entrada = dia + timedelta(
                    hours=h, minutes=rng.randint(0, 59), seconds=rng.randint(0, 59)
                )
                duracion_h = rng.uniform(0.5, 7.0)
                salida = entrada + timedelta(hours=duracion_h)
                costo = round(rng.uniform(800, 6000), 0)
                comun = dict(
                    patente_detectada=patente,
                    normalized_patente=patente.replace(" ", "").replace("-", "").upper(),
                    tipo_vehiculo=tipo,
                    sucursal=sucursal,
                    imagen_path=MARCA,
                    pago_confirmado=True,
                    metodo_pago=rng.choice(METODOS_PAGO),
                    ocr_time=round(rng.uniform(0.08, 0.45), 3),
                )
                db.add(AccessLog(
                    **comun, tipo_evento="ENTRADA", fecha_hora=entrada.isoformat(),
                    fecha_pago=entrada.isoformat(), costo_estadia=costo,
                ))
                db.add(AccessLog(
                    **comun, tipo_evento="SALIDA", fecha_hora=salida.isoformat(),
                    fecha_pago=salida.isoformat(), costo_estadia=costo,
                ))
                entradas += 1
                salidas += 1

    db.commit()
    return {"entradas": entradas, "salidas": salidas, "borrados": borrados}


def main():
    ap = argparse.ArgumentParser(description="Genera movimientos demo por sucursal")
    ap.add_argument("--dias", type=int, default=56)
    ap.add_argument("--por-dia", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    db = SessionLocal()
    try:
        res = generar(db, args.dias, args.por_dia, args.seed)
        print(f"movimientos generados: {res}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
