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
def manual_entry(plate: str, tipo_vehiculo: str = "Auto", floor_id: int = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
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
    
    # Manejo de Pisos
    floor = None
    if floor_id:
        floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
        if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
        
        if tipo_vehiculo == "Auto":
            floor.ocupacion_actual += 1
        else:
            floor.ocupacion_motos += 1
    else:
        # Fallback a aforo global de sede si no hay pisos
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if not aforo:
            aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
            db.add(aforo)
        
        if tipo_vehiculo == "Auto":
            aforo.ocupacion_actual += 1
        else:
            aforo.ocupacion_motos += 1

    db.add(models.AccessLog(
        patente_detectada=p, 
        tipo_evento="ENTRADA", 
        tipo_vehiculo=tipo_vehiculo, 
        fecha_hora=now.isoformat(), 
        sucursal=sucursal,
        floor_id=floor_id
    ))
    db.commit()
    return {"status": "ok", "message": f"Ingreso manual registrado en {floor.nombre if floor else 'Planta Baja'}: {p} ({tipo_vehiculo})"}

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
    if aforo:
        if ultimo.tipo_vehiculo == "Auto" and aforo.ocupacion_actual > 0:
            aforo.ocupacion_actual -= 1
        elif ultimo.tipo_vehiculo == "Moto" and aforo.ocupacion_motos > 0:
            aforo.ocupacion_motos -= 1
        
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="SALIDA", tipo_vehiculo=ultimo.tipo_vehiculo, fecha_hora=datetime.datetime.now().isoformat(), pago_confirmado=True, sucursal=sucursal))
    db.commit()
    return {"status": "ok", "message": f"Salida manual registrada en {sucursal or 'Global'}: {p}"}

@router.post("/cancel-stay")
def cancel_stay(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Cancela una estadía actual. Si está dentro de los 15 min de cortesía, no cobra."""
    from routes.parking import normalize_plate
    p = normalize_plate(plate)
    sucursal = staff.sucursal
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA":
        raise HTTPException(status_code=400, detail="El vehículo no figura como ingresado")
    
    # Verificar cortesía (15 minutos)
    entrada_dt = datetime.datetime.fromisoformat(ultimo.fecha_hora)
    minutos_transcurridos = (datetime.datetime.now() - entrada_dt).total_seconds() / 60
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo:
        if ultimo.tipo_vehiculo == "Auto" and aforo.ocupacion_actual > 0:
            aforo.ocupacion_actual -= 1
        elif ultimo.tipo_vehiculo == "Moto" and aforo.ocupacion_motos > 0:
            aforo.ocupacion_motos -= 1
    
    if minutos_transcurridos <= 15:
        # Cortesía: Salida sin cargo
        db.add(models.AccessLog(
            patente_detectada=p, 
            tipo_evento="SALIDA", 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=datetime.datetime.now().isoformat(), 
            pago_confirmado=True, 
            costo_estadia=0.0,
            sucursal=sucursal
        ))
        msg = f"Estadía cancelada (Cortesía: {int(minutos_transcurridos)} min). Sin cargo."
    else:
        # Excedió cortesía: Se debe cobrar
        if not ultimo.pago_confirmado:
            from services.billing_service import BillingService
            monto = BillingService.calculate_debt(ultimo.fecha_hora, db, sucursal=sucursal, tipo_vehiculo=ultimo.tipo_vehiculo)
            raise HTTPException(status_code=402, detail=f"Excedió cortesía ({int(minutos_transcurridos)} min). Debe abonar ${monto}")
        
        # Si ya pagó, registramos salida normal
        db.add(models.AccessLog(
            patente_detectada=p, 
            tipo_evento="SALIDA", 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=datetime.datetime.now().isoformat(), 
            pago_confirmado=True, 
            sucursal=sucursal
        ))
        msg = "Salida registrada con éxito."

    db.commit()
    return {"status": "ok", "message": msg}
