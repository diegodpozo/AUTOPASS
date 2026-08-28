import datetime
from sqlalchemy.orm import Session
import models
import schemas
from services.billing_service import BillingService
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.time_service import TimeService
from repositories.reservation_repository import ReservationRepository
from fastapi import HTTPException
from models.enums import ReservationStatus, PaymentStatus, VehicleType, AccessEventType
from core.logger import get_logger

logger = get_logger("ReservationService")

# --- HELPERS DE AFORO ---

def _normalizar_sucursal(text: str) -> str:
    if not text: return ""
    import unicodedata
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def verificar_disponibilidad(db: Session, sucursal_nombre: str, fecha_inicio: str, fecha_fin: str, exclude_id: int = None):
    """VERIFICA SI HAY LUGARES DISPONIBLES EN LA SUCURSAL PARA EL PERIODO SOLICITADO.
    RETORNA {disponible, capacidad_total, ocupada, mensaje}."""
    # 1. OBTENER CAPACIDAD TOTAL
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    capacidad_total = 0
    if branch and branch.floors:
        capacidad_total = sum(f.capacidad_total for f in branch.floors)
    else:
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first()
        if aforo:
            capacidad_total = aforo.capacidad_total

    if capacidad_total == 0:
        return {"disponible": True, "capacidad_total": 0, "ocupada": 0, "mensaje": "Sin datos de capacidad"}

    # 2. CONTAR RESERVAS QUE SE SUPERPOSICIONAN EN EL RANGO (EXCLUYENDO CANCELADAS/COMPLETADAS)
    #    SE CONSIDERAN ACTIVAS: Pendiente, Pagado, Activa, Confirmada
    query = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == sucursal_nombre,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.estado_pago.in_(["Pendiente", "Pagado"]),
        models.Reservation.fecha_inicio < fecha_fin,
        models.Reservation.fecha_fin > fecha_inicio
    )
    if exclude_id:
        query = query.filter(models.Reservation.id != exclude_id)

    ocupada = query.count()

    disponible = ocupada < capacidad_total
    restan = max(0, capacidad_total - ocupada)
    return {
        "disponible": disponible,
        "capacidad_total": capacidad_total,
        "ocupada": ocupada,
        "restan": restan,
        "mensaje": f"Quedan {restan} lugar{'es' if restan != 1 else ''} disponible{'s' if restan != 1 else ''}" if disponible else "No hay disponibilidad para el horario solicitado."
    }

def _reservar_plaza_en_aforo(db: Session, res: "models.Reservation"):
    """YA NO PRE-OCUPA PLAZA FISICA. La ocupación la maneja exclusivamente el ALPR (entrada/salida física)."""
    pass

def _liberar_plaza_en_aforo(db: Session, res: "models.Reservation"):
    """YA NO LIBERA PLAZA FISICA. La ocupación la maneja exclusivamente el ALPR (entrada/salida física)."""
    pass

# --- SERVICIO DE GESTION DE RESERVAS ---

class ReservationService:
    @staticmethod
    def create_reservation(db: Session, data: schemas.AdminReservationCreate) -> models.Reservation:
        """CREA UNA NUEVA RESERVA MANUAL DESDE EL PANEL ADMINISTRATIVO."""
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente).first()
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO

        monto = BillingService.calculate_total_amount(
            db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin, 
            sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_vehiculo
        )

        branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == data.sucursal_nombre).first()
        info_sede = f"{branch.direccion}. {'Abierto 24hs' if branch.is_24h else branch.horario}." if branch else "Sede no especificada."

        new_res = models.Reservation(
            user_id=data.user_id,
            patente=data.patente,
            fecha_inicio=data.fecha_inicio,
            fecha_fin=data.fecha_fin,
            monto_total=monto,
            estado_pago=PaymentStatus.PENDIENTE,
            estado_reserva=ReservationStatus.PENDIENTE,
            tipo_estadia=data.tipo_estadia,
            sucursal_nombre=data.sucursal_nombre,
            sucursal_info=info_sede,
            cliente_nombre=data.cliente_nombre
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        return new_res

    @staticmethod
    def update_reservation(db: Session, res_id: int, data: schemas.ReservationUpdate) -> models.Reservation:
        """ACTUALIZA LOS DATOS DE UNA RESERVA Y RECALCULA MONTOS SI ES NECESARIO."""
        res = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
        if not res:
            return None

        old_pago = res.estado_pago
        if data.patente: res.patente = data.patente.upper()
        if data.tipo_estadia: res.tipo_estadia = data.tipo_estadia
        if data.fecha_inicio: res.fecha_inicio = data.fecha_inicio
        if data.fecha_fin: res.fecha_fin = data.fecha_fin
        
        if hasattr(data, 'estado_pago') and data.estado_pago: res.estado_pago = data.estado_pago
        if hasattr(data, 'estado_reserva') and data.estado_reserva: res.estado_reserva = data.estado_reserva

        #RECALCULAR PUNTOS SI CAMBIA UN PAGADO
        if old_pago != PaymentStatus.PAGADO and res.estado_pago == PaymentStatus.PAGADO and res.user:
            puntos_ganados = BillingService.calculate_points(res.monto_total)
            res.user.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=res.user.id,
                cantidad=puntos_ganados,
                motivo=f"Edición Admin - Pago Reserva: {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))

        # RECALCULAR MONTO
        vehiculo = db.query(models.Vehicle).filter(models.Vehicle.patente == res.patente).first()
        tipo_vehiculo = vehiculo.tipo if vehiculo else VehicleType.AUTO
        
        res.monto_total = BillingService.calculate_total_amount(
            db, res.tipo_estadia, res.fecha_inicio, res.fecha_fin, 
            sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo
        )
        
        db.commit()
        db.refresh(res)
        return res

    @staticmethod
    def cleanup_overdue_reservations(db: Session):
        """CANCELA AUTOMATICAMENTE RESERVAS IMPAGAS CUYO TIEMPO DE INICIO YA PASO CON UN MARGEN DE GRACIA."""
        now = TimeService.now()
        grace_cutoff = now - datetime.timedelta(hours=2)
        cutoff_str = grace_cutoff.strftime("%Y-%m-%d %H:%M")
        
        overdue = db.query(models.Reservation).filter(
            models.Reservation.estado_pago == PaymentStatus.PENDIENTE,
            models.Reservation.estado_reserva == ReservationStatus.PENDIENTE,
            models.Reservation.fecha_inicio <= cutoff_str,
            models.Reservation.tipo_estadia == "hora"
        ).all()
        
        if overdue:
            logger.info(f"Cancelando {len(overdue)} reservas impagas vencidas. Cutoff: {cutoff_str}")
            for r in overdue:
                r.estado_reserva = ReservationStatus.CANCELADA
                r.estado_pago = PaymentStatus.FALLIDO
            db.commit()
            return len(overdue)
        return 0

    @staticmethod
    def auto_finalize_reservations(db: Session, user_id: int):
        """MARCA COMO COMPLETADAS LAS RESERVAS DE UN USUARIO CUYO TIEMPO DE ESTADIA YA EXPIRO."""
        now_str = TimeService.now_str()
        past_reservations = ReservationRepository.get_past_reservations(db, user_id, now_str)
        if past_reservations:
            for r in past_reservations:
                r.estado_reserva = ReservationStatus.COMPLETADA
            db.commit()

    @staticmethod
    def auto_finalize_all_reservations(db: Session):
        """MARCA COMO COMPLETADAS TODAS LAS RESERVAS VENCIDAS DEL SISTEMA."""
        now_str = TimeService.now_str()
        # BUSCAMOS RESERVAS QUE ESTEN PENDIENTES O ACTIVAS PERO CUYA FECHA_FIN YA PASO
        vencidas = db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin < now_str
        ).all()
        
        if vencidas:
            logger.info(f"Finalizando {len(vencidas)} reservas vencidas.")
            for r in vencidas:
                r.estado_reserva = ReservationStatus.COMPLETADA
                # LIBERAR PLAZA SI ES NO HORARIA (NUNCA SE LIBERA EN SALIDA FISICA)
                if r.tipo_estadia != "hora" and r.sucursal_nombre:
                    _liberar_plaza_en_aforo(db, r)
            db.commit()
            return len(vencidas)
        return 0

    @staticmethod
    def pay_reservation(db: Session, user: models.User, res_id: int):
        """ABONA UNA RESERVA UTILIZANDO EL SALDO DISPONIBLE DEL USUARIO."""
        res = ReservationRepository.get_by_user_and_id(db, user.id, res_id)
        
        if not res: 
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")

        if res.estado_pago == PaymentStatus.PAGADO:
            return {"status": "ok", "message": "La reserva ya ha sido abonada"}
        
        if user.saldo < res.monto_total:
            raise HTTPException(status_code=400, detail="Saldo insuficiente en su cuenta AutoPass")
        
        # DEDUCCION DE SALDO Y ACTUALIZACION DE ESTADO
        user.saldo -= res.monto_total
        res.estado_pago = PaymentStatus.PAGADO
        res.estado_reserva = ReservationStatus.ACTIVA
        res.fecha_pago = datetime.datetime.now().isoformat()
        
        # ACREDITACION DE PUNTOS POR LEALTAD
        puntos_ganados = BillingService.calculate_points(res.monto_total)
        user.puntos_acumulados += puntos_ganados
        
        db.add(models.PointsLog(
            user_id=user.id,
            cantidad=puntos_ganados,
            motivo=f"Reserva: {res.patente}",
            fecha=datetime.datetime.now().isoformat()
        ))
        
        db.commit()

        # RESERVAR PLAZA EN AFORO PARA RESERVAS NO HORARIAS (DIA/SEMANA/QUINCENA/MES)
        # SOLO SI LA RESERVA YA COMENZO; SI ES FUTURA, LO HARA EL WORKER AL INICIAR
        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            now_str = TimeService.now_str()
            if res.fecha_inicio <= now_str:
                _reservar_plaza_en_aforo(db, res)

        # ENVIAR MAIL DE CONFIRMACION
        res_info = {
            "id": res.id,
            "sucursal": res.sucursal_nombre,
            "direccion": res.sucursal_info,
            "patente": res.patente,
            "fecha_inicio": res.fecha_inicio,
            "fecha_fin": res.fecha_fin,
            "costo": res.monto_total
        }
        EmailService.send_reservation_confirmation(user.email, user.nombre, res_info)

        try:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user.id, "RESERVATION_CONFIRMED",
                f"Reserva #{res.id} confirmada",
                f"Se abonó con éxito tu reserva en {res.sucursal_nombre} por ${res.monto_total:,.2f}.",
                res.id
            )
            if puntos_ganados > 0:
                UserNotificationService.create_notification(
                    db, user.id, "POINTS_EARNED",
                    "¡Puntos AutoPass!",
                    f"¡Ganaste {puntos_ganados} puntos por abonar la reserva #{res.id} ({res.patente}).",
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar pago de reserva: {e}")

        return {"status": "ok", "message": "Reserva abonada con éxito", "puntos_ganados": puntos_ganados}

    @staticmethod
    def simulate_refund(db: Session, res: models.Reservation):
        """CALCULA EL REEMBOLSO POTENCIAL SIN EJECUTAR LA CANCELACION."""
        # 1. VERIFICACION DE PRESENCIA FISICA
        import re
        norm_pat = re.sub(r'[^A-Z0-9]', '', (res.patente or '').upper())
        vinc_log = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == norm_pat,
            models.AccessLog.tipo_evento == AccessEventType.ENTRADA,
            models.AccessLog.sucursal == res.sucursal_nombre
        ).order_by(models.AccessLog.id.desc()).first()

        es_presencial = False
        if vinc_log:
            salida = db.query(models.AccessLog).filter(
                models.AccessLog.patente_detectada == vinc_log.patente_detectada,
                models.AccessLog.tipo_evento == AccessEventType.SALIDA,
                models.AccessLog.id > vinc_log.id,
                models.AccessLog.sucursal == vinc_log.sucursal
            ).first()
            if not salida:
                es_presencial = True

        if es_presencial:
            return {"reembolso": 0.0, "error": "Vehículo en el predio"}

        # 2. CALCULO DE REEMBOLSO
        monto_a_reembolsar = 0.0
        if res.estado_pago == PaymentStatus.PAGADO:
            now = datetime.datetime.now()
            start = datetime.datetime.fromisoformat(res.fecha_inicio)
            end = datetime.datetime.fromisoformat(res.fecha_fin)

            if now < start:
                monto_a_reembolsar = res.monto_total
            elif now > end:
                monto_a_reembolsar = 0.0
            else:
                if res.tipo_estadia == "hora" and vinc_log:
                    monto_a_reembolsar = 0.0
                else:
                    duracion_total = (end - start).total_seconds()
                    tiempo_restante = (end - now).total_seconds()
                    if duracion_total > 0:
                        porcentaje_restante = max(0, tiempo_restante / duracion_total)
                        monto_a_reembolsar = round(res.monto_total * porcentaje_restante, 2)
        
        return {"reembolso": monto_a_reembolsar, "error": None}

    @staticmethod
    def cancel_reservation(db: Session, user: models.User, res_id: int):
        """CANCELA UNA RESERVA Y GESTIONA REEMBOLSOS PROPORCIONALES."""
        res = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
        
        if not res: 
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if res.estado_reserva == ReservationStatus.CANCELADA:
            return {"status": "ok", "message": "La reserva ya se encuentra cancelada"}
        
        if res.estado_reserva == ReservationStatus.COMPLETADA:
            return {"status": "error", "message": "La reserva ya finalizó y no puede cancelarse"}
            
        # USAMOS LA SIMULACION PARA OBTENER EL MONTO
        sim = ReservationService.simulate_refund(db, res)
        if sim["error"]:
            raise HTTPException(status_code=400, detail=sim["error"])
        
        monto_a_reembolsar = sim["reembolso"]

        # 3. EJECUCION DEL REEMBOLSO
        target_user = user or res.user
        if monto_a_reembolsar > 0 and target_user:
            target_user.saldo += monto_a_reembolsar
            
            # AJUSTE DE PUNTOS (SOLO SOBRE LO REEMBOLSADO)
            puntos_a_descontar = BillingService.calculate_points(monto_a_reembolsar)
            target_user.puntos_acumulados = max(0, target_user.puntos_acumulados - puntos_a_descontar)
            
            db.add(models.PointsLog(
                user_id=target_user.id,
                cantidad=-puntos_a_descontar,
                motivo=f"Reembolso por Cancelación (Proporcional): {res.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))

        res.estado_reserva = ReservationStatus.CANCELADA
        res.estado_pago = PaymentStatus.REEMBOLSADO if monto_a_reembolsar > 0 else PaymentStatus.CANCELADO
        res.monto_reembolsado = float(monto_a_reembolsar)
        
        if monto_a_reembolsar > 0:
            res.fecha_pago = datetime.datetime.now().isoformat()
            
        db.commit()

        if res.tipo_estadia != "hora" and res.sucursal_nombre:
            _liberar_plaza_en_aforo(db, res)
        
        msg = f"Reserva cancelada. Reembolso: ${monto_a_reembolsar}" if monto_a_reembolsar > 0 else "Reserva cancelada sin reembolso."
        
        try:
            from services.user_notification_service import UserNotificationService
            if target_user:
                notif_msg = f"Tu reserva #{res.id} en {res.sucursal_nombre} fue cancelada."
                if monto_a_reembolsar > 0:
                    notif_msg += f" Se reembolsaron ${monto_a_reembolsar:,.2f} a tu saldo."
                UserNotificationService.create_notification(
                    db, target_user.id, "RESERVATION_CANCELLED",
                    f"Reserva #{res.id} cancelada",
                    notif_msg,
                    res.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar cancelacion de reserva: {e}")

        return {"status": "ok", "message": msg, "reembolso": monto_a_reembolsar}
