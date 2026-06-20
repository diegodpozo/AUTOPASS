import datetime 
import json
import base64
import os
from sqlalchemy.orm import Session
from fastapi import Request
import models
import schemas
from core.config import settings
from models.enums import VehicleType, AccessEventType, ReservationStatus, PaymentStatus
from services.notification_service import NotificationService
import unicodedata

def normalize_name(text: str):
    if not text: return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class AccessService:
    @staticmethod
    def _save_image(plate: str, image_base64: str) -> str:
        if not image_base64:
            return None
        
        now = datetime.datetime.now()
        img_name = f"{plate}_{now.strftime('%H%M%S')}.jpg"
        if not os.path.exists(settings.IMAGE_DIR):
            os.makedirs(settings.IMAGE_DIR)
            
        with open(os.path.join(settings.IMAGE_DIR, img_name), "wb") as f:
            f.write(base64.b64decode(image_base64))
        return img_name

    @staticmethod
    def _publish_mqtt(request: Request, topic: str, payload: dict):
        if request and hasattr(request.app, 'mqtt_client'):
            request.app.mqtt_client.publish(topic, json.dumps(payload))

    @classmethod
    def validate_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None) -> dict:
        from routes.parking.utils import normalize_plate
        p = normalize_plate(data.plate)
        sucursal = data.gate_id.split('_')[0] if data.gate_id and '_' in data.gate_id else None
        if sucursal == "ENTRADA": sucursal = None
        
        ultimo = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == p,
            models.AccessLog.sucursal == sucursal
        ).order_by(models.AccessLog.id.desc()).first()
        
        if ultimo and ultimo.tipo_evento == AccessEventType.ENTRADA: 
            return {"status": "denied", "message": "El vehículo ya figura dentro de esta sede"}
        
        # DETERMINAR TIPO DE VEHICULO
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == p).first()
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

        now = datetime.datetime.now()
        img_name = cls._save_image(p, data.image_base64)
                
        # BUSCAMOS RESERVA PAGADA QUE ESTE EN EL RANGO DE TIEMPO ACTUAL
        now_str = now.isoformat()
        reserva = db.query(models.Reservation).filter(
            models.Reservation.patente == p, 
            models.Reservation.estado_pago == PaymentStatus.PAGADO,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_inicio <= now_str,
            models.Reservation.fecha_fin >= now_str
        ).filter(
            (models.Reservation.sucursal_nombre == sucursal) | (models.Reservation.sucursal_nombre == None)
        ).first()
        
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if not aforo:
            aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
            db.add(aforo)
        
        # VALIDAR CAPACIDAD SEGUN TIPO
        capacidad = aforo.capacidad_total if tipo_vehiculo == VehicleType.AUTO else aforo.capacidad_motos
        ocupacion = aforo.ocupacion_actual if tipo_vehiculo == VehicleType.AUTO else aforo.ocupacion_motos

        if reserva or ocupacion < capacidad:
            if tipo_vehiculo == VehicleType.AUTO:
                aforo.ocupacion_actual += 1
            else:
                aforo.ocupacion_motos += 1

            if reserva and reserva.estado_reserva == ReservationStatus.PENDIENTE: 
                reserva.estado_reserva = ReservationStatus.ACTIVA
                
            db.add(models.AccessLog(
                patente_detectada=p, 
                tipo_evento=AccessEventType.ENTRADA, 
                tipo_vehiculo=tipo_vehiculo,
                fecha_hora=now_str, 
                imagen_path=img_name, 
                reserva_id=reserva.id if reserva else None,
                sucursal=sucursal
            ))
            db.commit()
            NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
            
            cls._publish_mqtt(request, settings.MQTT_TOPIC_ENTRADA, {
                "command": "OPEN", 
                "plate": p, 
                "sucursal": sucursal,
                "timestamp": now.isoformat()
            })
                
            return {"status": "allowed", "action": "OPEN_GATE", "message": f"Acceso permitido en {sucursal or 'Global'}. Bienvenido {p}"}
        return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

    @classmethod
    def exit_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None) -> dict:
        from routes.parking.utils import normalize_plate
        p = normalize_plate(data.plate)
        sucursal = data.gate_id.split('_')[0] if data.gate_id and '_' in data.gate_id else None
        
        ultimo = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == p,
            models.AccessLog.sucursal == sucursal
        ).order_by(models.AccessLog.id.desc()).first()
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA: 
            return {"status": "error", "message": "El vehículo no tiene registro de ingreso en esta sede"}
        
        if not (ultimo.pago_confirmado or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO)):
            return {"status": "denied", "message": "Deuda pendiente de pago en esta sede"}
            
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if aforo:
            if ultimo.tipo_vehiculo == VehicleType.AUTO and aforo.ocupacion_actual > 0:
                aforo.ocupacion_actual -= 1
            elif ultimo.tipo_vehiculo == VehicleType.MOTO and aforo.ocupacion_motos > 0:
                aforo.ocupacion_motos -= 1
            
        now = datetime.datetime.now()
        db.add(models.AccessLog(
            patente_detectada=p, 
            tipo_evento=AccessEventType.SALIDA, 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=now.isoformat(), 
            pago_confirmado=True, 
            sucursal=sucursal
        ))
        db.commit()
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
        
        cls._publish_mqtt(request, settings.MQTT_TOPIC_SALIDA, {
            "command": "OPEN", 
            "plate": p, 
            "sucursal": sucursal,
            "timestamp": now.isoformat()
        })
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Salida autorizada en {sucursal or 'Global'}. Adiós {p}"}

    @classmethod
    def validate_qr(cls, db: Session, data: schemas.QRValidation, request: Request = None) -> dict:
        from routes.parking.utils import normalize_plate
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

            if reserva.estado_pago != PaymentStatus.PAGADO:
                return {"status": "denied", "message": "La reserva no ha sido abonada"}

            vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == patente_qr).first()
            tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

            now = datetime.datetime.now()
            gate_id = data.gate_id.upper() if data.gate_id else "ENTRADA"
            is_entry = "ENTRADA" in gate_id
            
            ultimo = db.query(models.AccessLog).filter(
                models.AccessLog.patente_detectada == reserva.patente,
                models.AccessLog.sucursal == sucursal
            ).order_by(models.AccessLog.id.desc()).first()

            if is_entry:
                if ultimo and ultimo.tipo_evento == AccessEventType.ENTRADA:
                    return {"status": "denied", "message": "El vehículo ya se encuentra dentro de esta sede"}
                
                if reserva.estado_reserva == ReservationStatus.COMPLETADA:
                     return {"status": "denied", "message": "Esta reserva ya expiró"}
                
                now_str = now.isoformat()
                if reserva.fecha_inicio > now_str or reserva.fecha_fin < now_str:
                    return {"status": "denied", "message": "La reserva no está vigente en este horario"}

                aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
                if not aforo:
                    aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
                    db.add(aforo)
                
                capacidad = aforo.capacidad_total if tipo_vehiculo == VehicleType.AUTO else aforo.capacidad_motos
                ocupacion = aforo.ocupacion_actual if tipo_vehiculo == VehicleType.AUTO else aforo.ocupacion_motos
                    
                if ocupacion >= capacidad:
                    return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

                if tipo_vehiculo == VehicleType.AUTO:
                    aforo.ocupacion_actual += 1
                else:
                    aforo.ocupacion_motos += 1

                if reserva.estado_reserva == ReservationStatus.PENDIENTE:
                    reserva.estado_reserva = ReservationStatus.ACTIVA

                db.add(models.AccessLog(
                    patente_detectada=reserva.patente, 
                    tipo_evento=AccessEventType.ENTRADA, 
                    tipo_vehiculo=tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=True, 
                    sucursal=sucursal
                ))
                db.commit()
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                cls._publish_mqtt(request, settings.MQTT_TOPIC_ENTRADA, {
                    "command": "OPEN", "plate": reserva.patente, "method": "QR", "sucursal": sucursal, "timestamp": now.isoformat()
                })
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Bienvenido {reserva.patente}"}
            else:
                if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
                    return {"status": "error", "message": "No se registra un ingreso activo para esta patente"}
                    
                aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
                if aforo:
                    if ultimo.tipo_vehiculo == VehicleType.AUTO and aforo.ocupacion_actual > 0:
                        aforo.ocupacion_actual -= 1
                    elif ultimo.tipo_vehiculo == VehicleType.MOTO and aforo.ocupacion_motos > 0:
                        aforo.ocupacion_motos -= 1
                
                db.add(models.AccessLog(
                    patente_detectada=reserva.patente, 
                    tipo_evento=AccessEventType.SALIDA, 
                    tipo_vehiculo=ultimo.tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=True, 
                    sucursal=sucursal
                ))
                db.commit()
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                cls._publish_mqtt(request, settings.MQTT_TOPIC_SALIDA, {
                    "command": "OPEN", "plate": reserva.patente, "method": "QR", "sucursal": sucursal, "timestamp": now.isoformat()
                })
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Adiós {reserva.patente}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error procesando QR: {str(e)}"}
