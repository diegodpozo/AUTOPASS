from core.database import SessionLocal
import models
from services.billing_service import BillingService

db = SessionLocal()
sucursal = "AUTOPASS Castelar"

q = db.query(models.AccessLog).filter(
    models.AccessLog.tipo_evento == "ENTRADA",
    models.AccessLog.sucursal == sucursal
)

entradas = q.all()
print(f"Checking {len(entradas)} entries for {sucursal}...")

for e in entradas:
    tiene_salida = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == e.patente_detectada, 
        models.AccessLog.tipo_evento == "SALIDA", 
        models.AccessLog.fecha_hora > e.fecha_hora,
        models.AccessLog.sucursal == e.sucursal
    ).first()
    
    if not tiene_salida:
        print(f"Parked: {e.patente_detectada}, ID: {e.id}, Ingreso: {e.fecha_hora}, Pago: {e.pago_confirmado}")

db.close()
