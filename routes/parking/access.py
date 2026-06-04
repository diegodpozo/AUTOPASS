import datetime
import json
import base64
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.config import settings
from services.billing_service import BillingService
from .utils import normalize_plate

router = APIRouter()

@router.post("/access/validate-plate", response_model=schemas.AccessResponse)
def validate_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida una patente detectada."""
    p = normalize_plate(data.plate)
    sucursal = data.gate_id.split('_')[0] if data.gate_id and '_' in data.gate_id else None
    if sucursal == "ENTRADA": sucursal = None
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if ultimo and ultimo.tipo_evento == "ENTRADA": 
        return {"status": "denied", "message": "El vehículo ya figura dentro de esta sede"}
    
    now = datetime.datetime.now()
    img_name = None
    if data.image_base64:
        img_name = f"{p}_{now.strftime('%H%M%S')}.jpg"
        if not os.path.exists(settings.IMAGE_DIR): os.makedirs(settings.IMAGE_DIR)
        with open(os.path.join(settings.IMAGE_DIR, img_name), "wb") as f: 
            f.write(base64.b64decode(data.image_base64))
            
    reserva = db.query(models.Reservation).filter(
        models.Reservation.patente == p, 
        models.Reservation.estado_reserva == "Pendiente"
    ).filter(
        (models.Reservation.sucursal_nombre == sucursal) | (models.Reservation.sucursal_nombre == None)
    ).first()
    
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if not aforo:
        aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0)
        db.add(aforo)
    
    if reserva or aforo.ocupacion_actual < aforo.capacidad_total:
        aforo.ocupacion_actual += 1
        if reserva: reserva.estado_reserva = "Activa"
        db.add(models.AccessLog(
            patente_detectada=p, 
            tipo_evento="ENTRADA", 
            fecha_hora=now.isoformat(), 
            imagen_path=img_name, 
            reserva_id=reserva.id if reserva else None,
            sucursal=sucursal
        ))
        db.commit()
        
        if request and hasattr(request.app, 'mqtt_client'):
            request.app.mqtt_client.publish(settings.MQTT_TOPIC_ENTRADA, json.dumps({
                "command": "OPEN", 
                "plate": p, 
                "sucursal": sucursal,
                "timestamp": now.isoformat()
            }))
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Acceso permitido en {sucursal or 'Global'}. Bienvenido {p}"}
    return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

@router.post("/access/exit-plate", response_model=schemas.AccessResponse)
def exit_plate(data: schemas.PlateValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida la salida de un vehículo."""
    p = normalize_plate(data.plate)
    sucursal = data.gate_id.split('_')[0] if data.gate_id and '_' in data.gate_id else None
    
    ultimo = db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada == p,
        models.AccessLog.sucursal == sucursal
    ).order_by(models.AccessLog.id.desc()).first()
    
    if not ultimo or ultimo.tipo_evento != "ENTRADA": 
        return {"status": "error", "message": "El vehículo no tiene registro de ingreso en esta sede"}
    
    if not (ultimo.pago_confirmado or (ultimo.reservation and ultimo.reservation.estado_pago == "Pagado")):
        return {"status": "denied", "message": "Deuda pendiente de pago en esta sede"}
        
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo and aforo.ocupacion_actual > 0: aforo.ocupacion_actual -= 1
        
    now = datetime.datetime.now()
    if ultimo.reservation: ultimo.reservation.estado_reserva = "Completada"
    db.add(models.AccessLog(patente_detectada=p, tipo_evento="SALIDA", fecha_hora=now.isoformat(), pago_confirmado=True, sucursal=sucursal))
    db.commit()
    
    if request and hasattr(request.app, 'mqtt_client'):
        request.app.mqtt_client.publish(settings.MQTT_TOPIC_SALIDA, json.dumps({
            "command": "OPEN", 
            "plate": p, 
            "sucursal": sucursal,
            "timestamp": now.isoformat()
        }))
        
    return {"status": "allowed", "action": "OPEN_GATE", "message": f"Salida autorizada en {sucursal or 'Global'}. Adiós {p}"}

@router.post("/access/validate-qr", response_model=schemas.AccessResponse)
def validate_qr(data: schemas.QRValidation, db: Session = Depends(get_db), request: Request = None):
    """Valida un Pase Digital (QR)."""
    try:
        sucursal = data.gate_id.split('_')[0] if data.gate_id and '_' in data.gate_id else None
        parts = data.qr_data.split('|')
        if len(parts) < 3 or parts[0] != "AUTOPASS":
            return {"status": "error", "message": "Formato de QR inválido"}
        
        reserva_id = int(parts[1].split(':')[1])
        patente_qr = normalize_plate(parts[2].split(':')[1])
        
        reserva = db.query(models.Reservation).filter(models.Reservation.id == reserva_id).first()
        if not reserva:
            return {"status": "error", "message": "Reserva no encontrada"}
        
        if normalize_plate(reserva.patente) != patente_qr:
            return {"status": "error", "message": "La patente del QR no coincide con la reserva"}

        if reserva.sucursal_nombre and sucursal and reserva.sucursal_nombre != sucursal:
            return {"status": "denied", "message": f"Esta reserva es válida únicamente para la sede {reserva.sucursal_nombre}"}

        if reserva.estado_pago != "Pagado":
            return {"status": "denied", "message": "La reserva no ha sido abonada"}

        now = datetime.datetime.now()
        gate_id = data.gate_id.upper() if data.gate_id else "ENTRADA"
        is_entry = "ENTRADA" in gate_id
        
        if is_entry:
            if reserva.estado_reserva == "Activa":
                return {"status": "denied", "message": "El vehículo ya se encuentra dentro de esta sede"}
            if reserva.estado_reserva == "Completada":
                 return {"status": "denied", "message": "Esta reserva ya fue utilizada y completada"}
            
            aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
            if not aforo:
                aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0)
                db.add(aforo)
                
            if aforo.ocupacion_actual >= aforo.capacidad_total:
                return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

            aforo.ocupacion_actual += 1
            reserva.estado_reserva = "Activa"
            db.add(models.AccessLog(patente_detectada=reserva.patente, tipo_evento="ENTRADA", fecha_hora=now.isoformat(), reserva_id=reserva.id, pago_confirmado=True, sucursal=sucursal))
            db.commit()
            
            if request and hasattr(request.app, 'mqtt_client'):
                request.app.mqtt_client.publish(settings.MQTT_TOPIC_ENTRADA, json.dumps({"command": "OPEN", "plate": reserva.patente, "method": "QR", "sucursal": sucursal, "timestamp": now.isoformat()}))
                
            return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Bienvenido {reserva.patente}"}
        else:
            if reserva.estado_reserva != "Activa":
                return {"status": "error", "message": "No se registra un ingreso activo para esta reserva"}
                
            aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
            if aforo and aforo.ocupacion_actual > 0: aforo.ocupacion_actual -= 1
            reserva.estado_reserva = "Completada"
            db.add(models.AccessLog(patente_detectada=reserva.patente, tipo_evento="SALIDA", fecha_hora=now.isoformat(), reserva_id=reserva.id, pago_confirmado=True, sucursal=sucursal))
            db.commit()
            
            if request and hasattr(request.app, 'mqtt_client'):
                request.app.mqtt_client.publish(settings.MQTT_TOPIC_SALIDA, json.dumps({"command": "OPEN", "plate": reserva.patente, "method": "QR", "sucursal": sucursal, "timestamp": now.isoformat()}))
                
            return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Adiós {reserva.patente}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Error procesando QR: {str(e)}"}

@router.post("/access/pay-stay")
def pay_stay(plate: str, db: Session = Depends(get_db)):
    """Procesa el pago de una estadía en curso."""
    result = BillingService.process_payment(db, normalize_plate(plate))
    if result["status"] == "ok": return result
    raise HTTPException(status_code=400, detail=result["message"])
