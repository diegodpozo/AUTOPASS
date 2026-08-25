import datetime 
import json
import base64
import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Request
import models
import schemas
from core.config import settings
from core.logger import get_logger
from models.enums import VehicleType, AccessEventType, ReservationStatus, PaymentStatus
from services.notification_service import NotificationService
from services.time_service import TimeService
from core.normalize import normalize_name

logger = get_logger("AccessService")

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
        # Log request for debugging ALPR integration
        try:
            logger.debug(f"validate_plate called. gate_id={getattr(data, 'gate_id', None)} plate_present={'plate' in data.__dict__}")
        except Exception:
            pass
        p = normalize_plate(data.plate)
        # Normalizar sucursal a partir de gate_id: intentar mapear a nombre completo en parking_branches
        sucursal = None
        if data.gate_id and '_' in data.gate_id:
            suc_short = normalize_name(data.gate_id.split('_')[0])
            try:
                branches = db.query(models.ParkingBranch).all()
                for b in branches:
                    if normalize_name(b.nombre) == suc_short:
                        sucursal = b.nombre
                        break
            except Exception:
                pass
        
        ultima_entrada = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == p,
            models.AccessLog.tipo_evento == AccessEventType.ENTRADA,
            models.AccessLog.sucursal == sucursal
        ).order_by(models.AccessLog.id.desc()).first()
        
        if ultima_entrada:
            tiene_salida = db.query(models.AccessLog.id).filter(
                models.AccessLog.patente_detectada == ultima_entrada.patente_detectada,
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.id > ultima_entrada.id,
                models.AccessLog.sucursal == sucursal
            ).first()
            if not tiene_salida:
                NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "error", p, "Vehículo ya dentro de esta sede", "error")
                return {"status": "denied", "message": "El vehículo ya figura dentro de esta sede"}
        
        # DETERMINAR TIPO DE VEHICULO (normalizando espacios en ambos lados)
        vehiculo = db.query(models.Vehicle).filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == p
        ).first()
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

        now = TimeService.now()
        img_name = cls._save_image(p, data.image_base64)
                
        # BUSCAMOS RESERVA PAGADA QUE ESTE EN EL RANGO DE TIEMPO ACTUAL
        now_str = now.strftime("%Y-%m-%d %H:%M")
        reserva = db.query(models.Reservation).filter(
            func.replace(func.upper(models.Reservation.patente), ' ', '') == p,
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
        if tipo_vehiculo == VehicleType.AUTO:
            capacidad = aforo.capacidad_total
            ocupacion = aforo.ocupacion_actual
        elif tipo_vehiculo == VehicleType.CAMIONETA:
            capacidad = getattr(aforo, 'capacidad_camionetas', 5)
            ocupacion = getattr(aforo, 'ocupacion_camionetas', 0)
        else:
            capacidad = aforo.capacidad_motos
            ocupacion = aforo.ocupacion_motos

        if reserva:
            if reserva.estado_reserva == ReservationStatus.PENDIENTE: 
                reserva.estado_reserva = ReservationStatus.ACTIVA
            if tipo_vehiculo == VehicleType.AUTO:
                aforo.ocupacion_actual += 1
            elif tipo_vehiculo == VehicleType.CAMIONETA:
                aforo.ocupacion_camionetas += 1
            else:
                aforo.ocupacion_motos += 1
        elif ocupacion < capacidad:
            if tipo_vehiculo == VehicleType.AUTO:
                aforo.ocupacion_actual += 1
            elif tipo_vehiculo == VehicleType.CAMIONETA:
                aforo.ocupacion_camionetas += 1
            else:
                aforo.ocupacion_motos += 1
        else:
            NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "error", p, "Capacidad máxima alcanzada", "error")
            return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}
            
        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento=AccessEventType.ENTRADA, 
            tipo_vehiculo=tipo_vehiculo,
            fecha_hora=now.isoformat(), 
            imagen_path=img_name, 
            reserva_id=reserva.id if reserva else None,
            pago_confirmado=True if (reserva and reserva.estado_pago == PaymentStatus.PAGADO) else False,
            sucursal=sucursal,
            ocr_time=data.ocr_time,
            backend_time=data.backend_time
        ))
        db.commit()
        logger.info(f"Notificando cambio de aforo para sucursal={sucursal}")
        NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "INGRESO", p, f"Bienvenido {p}", "ok")
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
        
        from services.hardware_service import HardwareService
        HardwareService.trigger_barrier("ENTRADA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Acceso permitido en {sucursal or 'Global'}. Bienvenido {p}"}

    @classmethod
    def exit_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None) -> dict:
        from routes.parking.utils import normalize_plate
        p = normalize_plate(data.plate)
        sucursal = None
        if data.gate_id and '_' in data.gate_id:
            suc_short = normalize_name(data.gate_id.split('_')[0])
            try:
                branches = db.query(models.ParkingBranch).all()
                for b in branches:
                    if normalize_name(b.nombre) == suc_short:
                        sucursal = b.nombre
                        break
            except Exception:
                pass

        ultimo = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == p,
            models.AccessLog.sucursal == sucursal
        ).order_by(models.AccessLog.id.desc()).first()
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA: 
            NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "error", p, "Sin registro de ingreso", "error")
            return {"status": "error", "message": "El vehículo no tiene registro de ingreso en esta sede"}
        
        if not (ultimo.pago_confirmado or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO)):
            fecha_str = ultimo.fecha_hora.replace(' ', 'T')
            entrada_dt = datetime.datetime.fromisoformat(fecha_str)
            minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
            if minutos_transcurridos > 10:
                NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "error", p, f"Deuda pendiente ({int(minutos_transcurridos)} min)", "error")
                return {"status": "denied", "message": f"Deuda pendiente de pago en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min"}
            
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if aforo:
            if ultimo.tipo_vehiculo == VehicleType.AUTO and aforo.ocupacion_actual > 0:
                aforo.ocupacion_actual -= 1
            elif ultimo.tipo_vehiculo == VehicleType.CAMIONETA and aforo.ocupacion_camionetas > 0:
                aforo.ocupacion_camionetas -= 1
            elif ultimo.tipo_vehiculo == VehicleType.MOTO and aforo.ocupacion_motos > 0:
                aforo.ocupacion_motos -= 1
            
            now = TimeService.now()
        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento=AccessEventType.SALIDA, 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=now.isoformat(), 
            pago_confirmado=True, 
            sucursal=sucursal,
            ocr_time=data.ocr_time,
            backend_time=data.backend_time
        ))
        db.commit()
        NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "SALIDA", p, f"Hasta luego {p}", "ok")
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
        
        from services.hardware_service import HardwareService
        HardwareService.trigger_barrier("SALIDA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Salida autorizada en {sucursal or 'Global'}. Adiós {p}"}

    @classmethod
    def validate_qr(cls, db: Session, data: schemas.QRValidation, request: Request = None) -> dict:
        from routes.parking.utils import normalize_plate
        # Log request for debugging QR integration
        try:
            logger.debug(f"validate_qr called. gate_id={getattr(data, 'gate_id', None)} qr_len={len(getattr(data, 'qr_data',''))}")
        except Exception:
            pass
        sucursal = None
        try:
            if data.gate_id and '_' in data.gate_id:
                suc_short = normalize_name(data.gate_id.split('_')[0])
            if suc_short not in ('ENTRADA', 'SALIDA'):
                sucursal = suc_short
            if sucursal:
                try:
                    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre.ilike(f"%{sucursal}%")).first()
                    if branch:
                        sucursal = branch.nombre
                except Exception:
                    pass
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

            vehiculo = db.query(models.Vehicle).filter(
                func.replace(func.upper(models.Vehicle.patente), ' ', '') == patente_qr
            ).first()
            tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

            now = TimeService.now()
            gate_id = data.gate_id.upper() if data.gate_id else "ENTRADA"
            is_entry = "EGRESO" not in gate_id and "SALIDA" not in gate_id
            
            ultimo = db.query(models.AccessLog).filter(
                models.AccessLog.patente_detectada == patente_qr,
                models.AccessLog.sucursal == sucursal
            ).order_by(models.AccessLog.id.desc()).first()

            if is_entry:
                if ultimo and ultimo.tipo_evento == AccessEventType.ENTRADA:
                    return {"status": "denied", "message": "El vehículo ya se encuentra dentro de esta sede"}
                
                if reserva.estado_reserva == ReservationStatus.COMPLETADA:
                     return {"status": "denied", "message": "Esta reserva ya expiró"}
                
                now_str = now.strftime("%Y-%m-%d %H:%M")
                if reserva.fecha_inicio > now_str or reserva.fecha_fin < now_str:
                    return {"status": "denied", "message": "La reserva no está vigente en este horario"}

                aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
                if not aforo:
                    aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
                    db.add(aforo)
                
                if tipo_vehiculo == VehicleType.AUTO:
                    capacidad = aforo.capacidad_total
                    ocupacion = aforo.ocupacion_actual
                elif tipo_vehiculo == VehicleType.CAMIONETA:
                    capacidad = getattr(aforo, 'capacidad_camionetas', 5)
                    ocupacion = getattr(aforo, 'ocupacion_camionetas', 0)
                else:
                    capacidad = aforo.capacidad_motos
                    ocupacion = aforo.ocupacion_motos
                    
                if not reserva and ocupacion >= capacidad:
                    return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

                if reserva:
                    if reserva.estado_reserva == ReservationStatus.PENDIENTE:
                        reserva.estado_reserva = ReservationStatus.ACTIVA
                    if tipo_vehiculo == VehicleType.AUTO:
                        aforo.ocupacion_actual += 1
                    elif tipo_vehiculo == VehicleType.CAMIONETA:
                        aforo.ocupacion_camionetas += 1
                    else:
                        aforo.ocupacion_motos += 1
                else:
                    if tipo_vehiculo == VehicleType.AUTO:
                        aforo.ocupacion_actual += 1
                    elif tipo_vehiculo == VehicleType.CAMIONETA:
                        aforo.ocupacion_camionetas += 1
                    else:
                        aforo.ocupacion_motos += 1

                db.add(models.AccessLog(
                    patente_detectada=normalize_plate(reserva.patente), 
                    normalized_patente=normalize_plate(reserva.patente),
                    tipo_evento=AccessEventType.ENTRADA, 
                    tipo_vehiculo=tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=True, 
                    sucursal=sucursal
                ))
                db.commit()
                logger.info(f"Notificando cambio de aforo (QR) para sucursal={sucursal}")
                NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "INGRESO", reserva.patente, f"QR - Bienvenido {reserva.patente}", "ok")
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                from services.hardware_service import HardwareService
                HardwareService.trigger_barrier("ENTRADA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Bienvenido {reserva.patente}"}
            else:
                if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
                    return {"status": "error", "message": "No se registra un ingreso activo para esta patente"}
                    
                aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
                if aforo:
                    if ultimo.tipo_vehiculo == VehicleType.AUTO and aforo.ocupacion_actual > 0:
                        aforo.ocupacion_actual -= 1
                    elif ultimo.tipo_vehiculo == VehicleType.CAMIONETA and aforo.ocupacion_camionetas > 0:
                        aforo.ocupacion_camionetas -= 1
                    elif ultimo.tipo_vehiculo == VehicleType.MOTO and aforo.ocupacion_motos > 0:
                        aforo.ocupacion_motos -= 1
                
                db.add(models.AccessLog(
                    patente_detectada=normalize_plate(reserva.patente), 
                    normalized_patente=normalize_plate(reserva.patente),
                    tipo_evento=AccessEventType.SALIDA, 
                    tipo_vehiculo=ultimo.tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=True, 
                    sucursal=sucursal
                ))
                db.commit()
                logger.info(f"Notificando cambio de aforo (QR SALIDA) para sucursal={sucursal}")
                NotificationService.set_last_event(normalize_name(sucursal) if sucursal else "GLOBAL", "SALIDA", reserva.patente, f"QR - Hasta luego {reserva.patente}", "ok")
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                from services.hardware_service import HardwareService
                HardwareService.trigger_barrier("SALIDA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Adiós {reserva.patente}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error procesando QR: {str(e)}"}
