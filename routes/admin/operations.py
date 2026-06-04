import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.security import get_operational_user

router = APIRouter()

@router.post("/open-barrier")
def open_barrier(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """Envía un comando de apertura manual a la barrera vía MQTT."""
    from core.config import settings
    
    topic = settings.MQTT_TOPIC_ENTRADA if gate_id.upper() == "ENTRADA" else settings.MQTT_TOPIC_SALIDA
    now = datetime.datetime.now().isoformat()
    
    if request and hasattr(request.app, 'mqtt_client'):
        request.app.mqtt_client.publish(topic, json.dumps({
            "command": "OPEN", 
            "method": "MANUAL_OP", 
            "staff_id": staff.id,
            "sucursal": staff.sucursal,
            "timestamp": now
        }))
        return {"status": "ok", "message": f"Comando de apertura enviado a {gate_id} ({staff.sucursal or 'Global'})"}
    
    raise HTTPException(status_code=503, detail="Servicio MQTT no disponible")

@router.post("/manual-entry")
def manual_entry(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Registra un ingreso forzado al predio de la sede."""
    from routes.parking import normalize_plate
    p = normalize_plate(plate)
    now = datetime.datetime.now()
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if ultimo and ultimo.tipo_evento == "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo ya figura como ingresado en esta sede")
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if not aforo:
        aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0)
        db.add(aforo)
    
    aforo.ocupacion_actual += 1
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="ENTRADA", fecha_hora=now.isoformat(), sucursal=sucursal))
    db.commit()
    return {"status": "ok", "message": f"Ingreso manual registrado en {sucursal or 'Global'}: {p}"}

@router.post("/manual-exit")
def manual_exit(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Registra una salida manual de la sede."""
    from routes.parking import normalize_plate
    p = normalize_plate(plate)
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo no figura en esta sede")
    
    if not ultimo.pago_confirmado:
        raise HTTPException(status_code=403, detail="DEUDA PENDIENTE en esta sede.")
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo and aforo.ocupacion_actual > 0: 
        aforo.ocupacion_actual -= 1
        
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="SALIDA", fecha_hora=datetime.datetime.now().isoformat(), pago_confirmado=True, sucursal=sucursal))
    db.commit()
    return {"status": "ok", "message": f"Salida manual registrada en {sucursal or 'Global'}: {p}"}
