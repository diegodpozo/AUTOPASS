import datetime 
import json
import base64
import os
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException
import models
import schemas
from core.config import settings
from core.logger import get_logger
from models.enums import VehicleType, AccessEventType, ReservationStatus, PaymentStatus
from services.access_occupancy import AccessOccupancyMixin
from services.notification_service import NotificationService
from services.time_service import TimeService
from core.normalize import normalize_name, normalize_plate, is_valid_plate
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.reservation_repository import ReservationRepository
from repositories.scoping import organization_of_sede
from repositories.vehicle_repository import VehicleRepository
from repositories.user_repository import UserRepository

logger = get_logger("AccessService")

class AccessService(AccessOccupancyMixin):
    """Flujos de acceso físico: entrada/salida ALPR, QR de reservas y operaciones manuales."""

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

    @staticmethod
    def _sede_desde_gate(db: Session, gate_id: str, organization_id=None):
        """SEDE (ParkingBranch) A LA QUE PERTENECE UN GATE ALPR (prefijo antes del '_').

        Atribucion gate -> sede -> empresa: con `organization_id` (binding del nodo)
        solo busca entre las sedes de esa empresa; sin el, si varias empresas tienen
        una sede con ese prefijo devuelve None porque no seria atribuible a nadie."""
        if gate_id and '_' in gate_id:
            suc_short = normalize_name(gate_id.split('_')[0])
            if suc_short:
                try:
                    candidatas = [
                        b for b in BranchRepository.get_all(db, organization_id=organization_id)
                        if normalize_name(b.nombre) == suc_short
                    ]
                except Exception:
                    logger.warning("[ACCESS] Error buscando sucursal por gate_id", exc_info=True)
                    return None
                if not candidatas:
                    return None
                if organization_id is not None:
                    return candidatas[0]
                orgs = {b.organization_id for b in candidatas}
                return candidatas[0] if len(orgs) == 1 else None
        return None

    @staticmethod
    def _branch_from_gate_id(db: Session, gate_id: str, organization_id=None) -> str:
        """Resuelve la sucursal completa a partir del prefijo del gate_id (ALPR)."""
        sede = AccessService._sede_desde_gate(db, gate_id, organization_id)
        return sede.nombre if sede else None

    @staticmethod
    def _alcance_gate(db: Session, gate_id: str, organization_id=None):
        """(SEDE, ORGANIZACION) DERIVADOS DEL GATE PARA UN FLUJO DE ACCESO.

        Prioriza el binding de la organizacion del nodo ALPR; si no lo hay, la
        organizacion sale de la sede resuelta (gate -> sede -> empresa)."""
        sede = AccessService._sede_desde_gate(db, gate_id, organization_id)
        if organization_id is None and sede is not None:
            organization_id = sede.organization_id
        return sede, organization_id

    @staticmethod
    def _alcance_logs(sucursal: str, organization_id=None):
        """ORGANIZACION P/ FILTRAR LOGS: solo cuando hubo sede resuelta (si no no hay atribucion)."""
        return organization_id if sucursal else None

    @staticmethod
    def _unclosed_last_entry(db: Session, p: str, sucursal: str, organization_id=None):
        """Último ingreso físico de la patente que no tiene salida posterior (sigue dentro)."""
        org_log = AccessService._alcance_logs(sucursal, organization_id)
        ultima_entrada = AccessRepository.get_last_entry(db, p, sucursal, organization_id=org_log)
        if ultima_entrada:
            tiene_salida = AccessRepository.get_exit_after(db, ultima_entrada.patente_detectada, ultima_entrada.id, sucursal, organization_id=org_log)
            if not tiene_salida:
                return ultima_entrada
        return None

    @staticmethod
    def _get_aforo(db: Session, sucursal: str):
        return BranchRepository.get_aforo_by_sucursal(db, sucursal)

    @staticmethod
    def _get_or_create_aforo(db: Session, sucursal: str):
        aforo = AccessService._get_aforo(db, sucursal)
        if not aforo:
            aforo = models.ParkingAforo(sucursal=sucursal, capacidad_total=20, ocupacion_actual=0, capacidad_motos=10, ocupacion_motos=0)
            db.add(aforo)
        return aforo

    @staticmethod
    def _suc_key(sucursal: str) -> str:
        """Clave normalizada de sucursal para notificaciones (GLOBAL si es None)."""
        return normalize_name(sucursal) if sucursal else "GLOBAL"

    @classmethod
    def _emit_pending_exit(cls, db: Session, log: models.AccessLog, plate: str, sucursal: str, data=None):
        """Avisa al dashboard (popup de caja) que un vehiculo intento salir con deuda pendiente.
        Incluye usuario registrado (o invitado), monto a cobrar, foto (id del log de entrada) y sucursal."""
        from services.billing_service import BillingService
        try:
            deuda = BillingService.preview_pending_amount(db, log)
            usuario = None
            vehiculo = VehicleRepository.get_by_normalized_patente_with_active_owner(db, plate)
            if vehiculo and vehiculo.owner:
                usuario = " ".join(filter(None, [vehiculo.owner.nombre, vehiculo.owner.apellido])).strip() or vehiculo.owner.email
            tipo = log.tipo_vehiculo.value if hasattr(log.tipo_vehiculo, "value") else str(log.tipo_vehiculo)
            payload = {
                "patente": plate,
                "log_id": log.id,
                "deuda": deuda,
                "usuario": usuario,
                "es_registrado": bool(usuario),
                "tipo_vehiculo": tipo,
                "sucursal": sucursal,
                "gate_id": getattr(data, "gate_id", None) or "SALIDA",
            }
            NotificationService.notify_pending_exit(cls._suc_key(sucursal), payload)
        except Exception:
            logger.warning("[ACCESS] Error emitiendo evento de salida impaga", exc_info=True)

    @classmethod
    def validate_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None, organization_id: int = None) -> dict:

        # Log request for debugging ALPR integration
        try:
            logger.debug(f"validate_plate called. gate_id={getattr(data, 'gate_id', None)} plate_present={'plate' in data.__dict__}")
        except Exception:
            logger.warning("[ACCESS] Error logueando validate_plate", exc_info=True)
        p = normalize_plate(data.plate)
        sede, org = cls._alcance_gate(db, data.gate_id, organization_id)
        if organization_id is not None and sede is None:
            # Nodo ligado a una empresa: un gate que no pertenece a ninguna de sus sedes.
            return {"status": "denied", "message": "Gate no habilitado para esta organización"}
        sucursal = sede.nombre if sede else None

        # RECHAZAR PATENTES CON FORMATO NO RECONOCIDO (NO GENERA REGISTRO)
        if not is_valid_plate(p):
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Formato de patente inválido", "error")
            return {"status": "denied", "message": "Formato de patente inválido. Ingreso denegado"}

        ultima_entrada = cls._unclosed_last_entry(db, p, sucursal, organization_id=org)
        if ultima_entrada:
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Vehículo ya dentro de esta sede", "error")
            return {"status": "denied", "message": "El vehículo ya figura dentro de esta sede"}
        
        # DETERMINAR TIPO DE VEHICULO (normalizando espacios en ambos lados)
        vehiculo = VehicleRepository.get_by_normalized_patente(db, p)
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

        now = TimeService.now()
        img_name = cls._save_image(p, data.image_base64)
                
        # BUSCAMOS RESERVA VIGENTE (PAGADA O IMPAGA) QUE ESTE EN EL RANGO DE TIEMPO ACTUAL
        now_str = now.strftime("%Y-%m-%d %H:%M")
        reserva = ReservationRepository.get_active_in_range_by_normalized_patente(db, p, now_str, sucursal, organization_id=org)
        
        aforo = cls._get_or_create_aforo(db, sucursal)
        
        # VALIDAR CAPACIDAD SEGUN TIPO
        capacidad, ocupacion = cls._capacidad_por_tipo(aforo, tipo_vehiculo)

        if reserva:
            if reserva.estado_reserva == ReservationStatus.PENDIENTE: 
                reserva.estado_reserva = ReservationStatus.ACTIVA
            cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=True)
        elif ocupacion < capacidad:
            cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=False)
        else:
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Capacidad máxima alcanzada", "error")
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
            ocr_time=data.ocr_time
        ))
        db.commit()
        logger.info(f"Notificando cambio de aforo para sucursal={sucursal}")
        NotificationService.set_last_event(cls._suc_key(sucursal), "INGRESO", p, f"Bienvenido {p}", "ok")
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
        
        from services.hardware_service import HardwareService
        HardwareService.trigger_barrier("ENTRADA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Acceso permitido en {sucursal or 'Global'}. Bienvenido {p}"}

    @classmethod
    def exit_plate(cls, db: Session, data: schemas.PlateValidation, request: Request = None, organization_id: int = None) -> dict:
        p = normalize_plate(data.plate)
        sede, org = cls._alcance_gate(db, data.gate_id, organization_id)
        if organization_id is not None and sede is None:
            return {"status": "denied", "message": "Gate no habilitado para esta organización"}
        sucursal = sede.nombre if sede else None

        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, org))
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA: 
            NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, "Sin registro de ingreso", "error")
            return {"status": "error", "message": "El vehículo no tiene registro de ingreso en esta sede"}
        
        if not (ultimo.pago_confirmado or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO)):
            fecha_str = ultimo.fecha_hora.replace(' ', 'T')
            entrada_dt = datetime.datetime.fromisoformat(fecha_str)
            minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
            if minutos_transcurridos > 10:
                NotificationService.set_last_event(cls._suc_key(sucursal), "error", p, f"Deuda pendiente ({int(minutos_transcurridos)} min)", "error")
                cls._emit_pending_exit(db, ultimo, p, sucursal, data)
                return {"status": "denied", "message": f"Deuda pendiente de pago en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min"}
            
        now = TimeService.now()
        aforo = cls._get_aforo(db, sucursal)
        if aforo:
            es_reserva = bool(ultimo.reserva_id or (ultimo.reservation and ultimo.reservation.estado_pago == PaymentStatus.PAGADO))
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, es_reserva)
            
        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento=AccessEventType.SALIDA, 
            tipo_vehiculo=ultimo.tipo_vehiculo,
            fecha_hora=now.isoformat(), 
            pago_confirmado=ultimo.pago_confirmado, 
            sucursal=sucursal,
            ocr_time=data.ocr_time
        ))
        db.commit()
        NotificationService.set_last_event(cls._suc_key(sucursal), "SALIDA", p, f"Hasta luego {p}", "ok")
        NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
        
        from services.hardware_service import HardwareService
        HardwareService.trigger_barrier("SALIDA", "OPEN", method="ALPR", details={"plate": p, "sucursal": sucursal}, request=request)
            
        return {"status": "allowed", "action": "OPEN_GATE", "message": f"Salida autorizada en {sucursal or 'Global'}. Adiós {p}"}

    @classmethod
    def validate_qr(cls, db: Session, data: schemas.QRValidation, request: Request = None, organization_id: int = None) -> dict:
        # Log request for debugging QR integration
        try:
            logger.debug(f"validate_qr called. gate_id={getattr(data, 'gate_id', None)} qr_len={len(getattr(data, 'qr_data',''))}")
        except Exception:
            logger.warning("[ACCESS] Error logueando validate_qr", exc_info=True)
        sucursal = None
        org = None
        try:
            if data.gate_id and '_' in data.gate_id:
                suc_short = normalize_name(data.gate_id.split('_')[0])
            else:
                suc_short = None
            if suc_short and suc_short not in (AccessEventType.ENTRADA.value, AccessEventType.SALIDA.value):
                if organization_id is not None and cls._sede_desde_gate(db, data.gate_id, organization_id) is None:
                    # Binding del nodo ALPR: el gate no corresponde a ninguna sede de la empresa.
                    return {"status": "denied", "message": "Gate no habilitado para esta organización"}
                sucursal = suc_short
            if sucursal:
                try:
                    branch = BranchRepository.get_by_name_like(db, sucursal, organization_id)
                    if branch:
                        sucursal = branch.nombre
                except Exception:
                    logger.warning("[ACCESS] Error resolviendo sucursal por nombre", exc_info=True)
            # ATRIBUCION gate -> sede -> empresa (para acotar logs y reserva)
            org = organization_id or (organization_of_sede(db, branch_name=sucursal) if sucursal else None)
            org_log = cls._alcance_logs(sucursal, org)
            parts = data.qr_data.split('|')
            if len(parts) < 3 or parts[0] != "AUTOPASS":
                return {"status": "error", "message": "Formato de QR inválido"}
            
            reserva_id = int(parts[1].split(':')[1])
            patente_qr = normalize_plate(parts[2].split(':')[1])
            
            reserva = ReservationRepository.get_by_id(db, reserva_id)
            if not reserva:
                return {"status": "error", "message": "Reserva no encontrada"}
            
            if normalize_plate(reserva.patente) != patente_qr:
                return {"status": "error", "message": "La patente del QR no coincide con la reserva"}

            if reserva.sucursal_nombre and sucursal and reserva.sucursal_nombre != sucursal:
                return {"status": "denied", "message": f"Esta reserva es válida únicamente para la sede {reserva.sucursal_nombre}"}

            # Aislamiento multiempresa: la reserva debe poder atribuirse a la empresa del gate.
            if org is not None and organization_of_sede(db, branch_id=reserva.sucursal_id, branch_name=reserva.sucursal_nombre) != org:
                return {"status": "denied", "message": "Esta reserva no pertenece a esta organización"}

            pagada = reserva.estado_pago == PaymentStatus.PAGADO

            vehiculo = VehicleRepository.get_by_normalized_patente(db, patente_qr)
            tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

            now = TimeService.now()
            gate_id = data.gate_id.upper() if data.gate_id else "ENTRADA"
            is_entry = "EGRESO" not in gate_id and "SALIDA" not in gate_id
            
            ultimo = AccessRepository.get_last_detected_by_patente_and_sucursal(db, patente_qr, sucursal, organization_id=org_log)

            if is_entry:
                if ultimo and ultimo.tipo_evento == AccessEventType.ENTRADA:
                    return {"status": "denied", "message": "El vehículo ya se encuentra dentro de esta sede"}
                
                if reserva.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
                     return {"status": "denied", "message": "Esta reserva ya expiró o fue cancelada"}
                
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                if reserva.fecha_inicio > now_str or reserva.fecha_fin < now_str:
                    return {"status": "denied", "message": "La reserva no está vigente en este horario"}

                aforo = cls._get_or_create_aforo(db, sucursal)
                
                capacidad, ocupacion = cls._capacidad_por_tipo(aforo, tipo_vehiculo)
                    
                if not reserva and ocupacion >= capacidad:
                    return {"status": "denied", "message": "Capacidad máxima alcanzada en esta sede"}

                if reserva:
                    if reserva.estado_reserva == ReservationStatus.PENDIENTE:
                        reserva.estado_reserva = ReservationStatus.ACTIVA
                    cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=True)
                else:
                    cls._asignar_plaza(aforo, tipo_vehiculo, es_reserva=False)

                db.add(models.AccessLog(
                    patente_detectada=normalize_plate(reserva.patente), 
                    normalized_patente=normalize_plate(reserva.patente),
                    tipo_evento=AccessEventType.ENTRADA, 
                    tipo_vehiculo=tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=pagada, 
                    sucursal=sucursal
                ))
                db.commit()
                logger.info(f"Notificando cambio de aforo (QR) para sucursal={sucursal}")
                NotificationService.set_last_event(cls._suc_key(sucursal), "INGRESO", reserva.patente, f"QR - Bienvenido {reserva.patente}", "ok")
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                from services.hardware_service import HardwareService
                HardwareService.trigger_barrier("ENTRADA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Bienvenido {reserva.patente}"}
            else:
                if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
                    return {"status": "error", "message": "No se registra un ingreso activo para esta patente"}

                if not (ultimo.pago_confirmado or reserva.estado_pago == PaymentStatus.PAGADO):
                    fecha_str = ultimo.fecha_hora.replace(' ', 'T')
                    entrada_dt = datetime.datetime.fromisoformat(fecha_str)
                    minutos_transcurridos = (now - entrada_dt).total_seconds() / 60
                    if minutos_transcurridos > 10:
                        NotificationService.set_last_event(cls._suc_key(sucursal), "error", patente_qr, f"Deuda pendiente de reserva impaga ({int(minutos_transcurridos)} min)", "error")
                        return {"status": "denied", "message": f"Deuda pendiente de pago en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min"}

                aforo = cls._get_aforo(db, sucursal)
                if aforo:
                    es_reserva = bool(ultimo.reserva_id or getattr(reserva, 'id', None))
                    cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, es_reserva)
                
                db.add(models.AccessLog(
                    patente_detectada=normalize_plate(reserva.patente), 
                    normalized_patente=normalize_plate(reserva.patente),
                    tipo_evento=AccessEventType.SALIDA, 
                    tipo_vehiculo=ultimo.tipo_vehiculo,
                    fecha_hora=now.isoformat(), 
                    reserva_id=reserva.id, 
                    pago_confirmado=ultimo.pago_confirmado, 
                    sucursal=sucursal
                ))
                db.commit()
                logger.info(f"Notificando cambio de aforo (QR SALIDA) para sucursal={sucursal}")
                NotificationService.set_last_event(cls._suc_key(sucursal), "SALIDA", reserva.patente, f"QR - Hasta luego {reserva.patente}", "ok")
                NotificationService.notify_occupancy_change(db, normalize_name(sucursal))
                
                from services.hardware_service import HardwareService
                HardwareService.trigger_barrier("SALIDA", "OPEN", method="QR", details={"plate": reserva.patente, "sucursal": sucursal}, request=request)
                    
                return {"status": "allowed", "action": "OPEN_GATE", "message": f"QR Válido en {sucursal or 'Global'}. Adiós {reserva.patente}"}
                
        except HTTPException:
            raise
        except Exception:
            logger.error("[ACCESS] Error inesperado procesando el pase digital", exc_info=True)
            return {"status": "error", "message": "Error interno procesando el pase digital"}

    @classmethod
    def manual_entry(cls, db: Session, plate: str, sucursal: str, tipo_vehiculo: str = "Auto", floor_id: int = None, request: Request = None, organization_id: int = None) -> dict:
        """Registra un ingreso manual forzado por personal staff/admin."""
        p = normalize_plate(plate)
        if not is_valid_plate(p):
            raise HTTPException(status_code=400, detail="Formato de patente inválido.")
        org = cls._alcance_logs(sucursal, organization_id)
        now = TimeService.now()
        
        # Buscar la última ENTRADA y verificar si el vehículo sigue adentro
        ultima_entrada = cls._unclosed_last_entry(db, p, sucursal, organization_id=org)
        if ultima_entrada:
            return {"status": "ok", "message": "El vehículo ya figura como ingresado en esta sede; se reutilizó el registro", "access_log_id": ultima_entrada.id}
        
        # Buscar reserva vigente (pagada o impaga)
        now_str = now.strftime("%Y-%m-%d %H:%M")
        reserva = ReservationRepository.get_active_in_range_by_normalized_patente(db, p, now_str, sucursal, organization_id=org)

        floor = None
        if floor_id:
            floor = BranchRepository.get_floor_by_id(db, floor_id)
            if not floor:
                raise HTTPException(status_code=404, detail="Piso no encontrado")
            cls._asignar_plaza(floor, tipo_vehiculo, bool(reserva))
        else:
            aforo = cls._get_or_create_aforo(db, sucursal)
            cls._asignar_plaza(aforo, tipo_vehiculo, bool(reserva))

        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento=AccessEventType.ENTRADA, 
            tipo_vehiculo=tipo_vehiculo, 
            fecha_hora=now.isoformat(), 
            sucursal=sucursal,
            floor_id=floor_id,
            reserva_id=reserva.id if reserva else None,
            pago_confirmado=True if (reserva and reserva.estado_pago == PaymentStatus.PAGADO) else False
        ))
        db.commit()

        try:
            from services.hardware_service import HardwareService
            norm = normalize_name(sucursal)
            logger.info(f"Notificando cambio de aforo (manual entry) para sucursal={sucursal} norm={norm}")
            NotificationService.notify_occupancy_change(db, norm)
            HardwareService.trigger_barrier("ENTRADA", "OPEN", method="MANUAL_ENTRY", details={"plate": p, "sucursal": sucursal}, request=request)
        except Exception as e:
            logger.error(f"Error notifying occupancy/hardware: {e}")

        return {"status": "ok", "message": f"Ingreso manual registrado en {floor.nombre if floor else 'Planta Baja'}: {p} ({tipo_vehiculo})"}

    @classmethod
    def manual_exit(cls, db: Session, plate: str, sucursal: str, request: Request = None, organization_id: int = None) -> dict:
        """Registra una salida manual forzada por personal staff/admin."""
        p = normalize_plate(plate)
        
        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, organization_id))
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
            raise HTTPException(status_code=400, detail="El vehículo no figura en esta sede")
        
        fecha_str = ultimo.fecha_hora.replace(' ', 'T')
        entrada_dt = datetime.datetime.fromisoformat(fecha_str)
        minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
        dentro_cortesia = minutos_transcurridos <= 10
        
        if not ultimo.pago_confirmado and not dentro_cortesia:
            raise HTTPException(status_code=403, detail=f"DEUDA PENDIENTE en esta sede. Cortesía: 10 min, transcurridos: {int(minutos_transcurridos)} min")
        
        aforo = cls._get_aforo(db, sucursal)
        if aforo:
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))

        if ultimo.floor_id:
            floor = BranchRepository.get_floor_by_id(db, ultimo.floor_id)
            if floor:
                cls._liberar_plaza(floor, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))

        db.add(models.AccessLog(
            patente_detectada=p, 
            normalized_patente=p,
            tipo_evento=AccessEventType.SALIDA, 
            tipo_vehiculo=ultimo.tipo_vehiculo, 
            fecha_hora=TimeService.now().isoformat(), 
            pago_confirmado=ultimo.pago_confirmado, 
            costo_estadia=0.0 if dentro_cortesia else None,
            metodo_pago="CAJA" if not dentro_cortesia else None,
            sucursal=sucursal,
            floor_id=ultimo.floor_id
        ))
        db.commit()

        try:
            from services.hardware_service import HardwareService
            norm = normalize_name(sucursal)
            logger.info(f"Notificando cambio de aforo (manual exit) para sucursal={sucursal} norm={norm}")
            NotificationService.notify_occupancy_change(db, norm)
            HardwareService.trigger_barrier("SALIDA", "OPEN", method="MANUAL_EXIT", details={"plate": p, "sucursal": sucursal}, request=request)
        except Exception as e:
            logger.error(f"Error notifying occupancy/hardware: {e}")

        msg = f"Salida manual registrada en {sucursal or 'Global'}: {p}" + (" (Cortesía)" if dentro_cortesia else "")
        return {"status": "ok", "message": msg}

    @classmethod
    def cancel_stay(cls, db: Session, plate: str, sucursal: str, organization_id: int = None) -> dict:
        """Cancela una estadía activa del vehículo."""
        from services.user_notification_service import UserNotificationService
        p = normalize_plate(plate)
        
        ultimo = AccessRepository.get_last_by_patente_and_sucursal(db, p, sucursal, organization_id=cls._alcance_logs(sucursal, organization_id))
        
        if not ultimo or ultimo.tipo_evento != AccessEventType.ENTRADA:
            raise HTTPException(status_code=400, detail="El vehículo no figura como ingresado")
        
        fecha_str = ultimo.fecha_hora.replace(' ', 'T')
        entrada_dt = datetime.datetime.fromisoformat(fecha_str)
        minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
        
        aforo = cls._get_aforo(db, sucursal)
        if aforo:
            cls._liberar_plaza(aforo, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))

        if ultimo.floor_id:
            floor = BranchRepository.get_floor_by_id(db, ultimo.floor_id)
            if floor:
                cls._liberar_plaza(floor, ultimo.tipo_vehiculo, bool(ultimo.reserva_id))
        
        if minutos_transcurridos <= 10:
            db.add(models.AccessLog(
                patente_detectada=p, 
                normalized_patente=p,
                tipo_evento=AccessEventType.SALIDA, 
                tipo_vehiculo=ultimo.tipo_vehiculo,
                fecha_hora=TimeService.now().isoformat(), 
                pago_confirmado=False, 
                costo_estadia=0.0,
                sucursal=sucursal
            ))
            msg = f"Estadía cancelada (Cortesía: {int(minutos_transcurridos)} min). Sin cargo."
        else:
            if not ultimo.pago_confirmado:
                from services.billing_service import BillingService
                monto = BillingService.calculate_debt(ultimo.fecha_hora, db, sucursal=sucursal, tipo_vehiculo=ultimo.tipo_vehiculo)
                if monto is None:
                    raise HTTPException(status_code=409, detail="La sucursal no tiene tarifario configurado. No se puede calcular el monto de la estadía.")
                raise HTTPException(status_code=402, detail=f"Excedió cortesía ({int(minutos_transcurridos)} min). Debe abonar ${monto}")
            
            db.add(models.AccessLog(
                patente_detectada=p, 
                normalized_patente=p,
                tipo_evento=AccessEventType.SALIDA, 
                tipo_vehiculo=ultimo.tipo_vehiculo,
                fecha_hora=TimeService.now().isoformat(), 
                pago_confirmado=True, 
                sucursal=sucursal
            ))
            msg = "Salida registrada con éxito."

        db.commit()

        try:
            vehicle = VehicleRepository.get_by_normalized_patente(db, p)
            if vehicle and vehicle.user_id:
                owner = UserRepository.get_by_id(db, vehicle.user_id)
                if owner and owner.rol == models.enums.UserRole.USER:
                    UserNotificationService.create_notification(
                        db, user_id=owner.id,
                        tipo=models.enums.NotificationType.STAY_CANCELLED_ADMIN,
                        titulo="Estadía cancelada",
                        mensaje=f"Un administrador canceló tu estadía en {sucursal} para la patente {plate}."
                    )
        except Exception:
            logger.warning("[ACCESS] Error notificando cancelación de estadía", exc_info=True)

        return {"status": "ok", "message": msg}