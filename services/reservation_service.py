import datetime
import math
import re

import models
import schemas
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.logger import get_logger
from core.normalize import format_plate, normalize_name as _normalizar_sucursal
from models.enums import PaymentStatus, ReservationStatus, UserRole, VehicleType
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.redemption_repository import RedemptionRepository
from repositories.reservation_repository import ReservationRepository
from repositories.user_repository import UserRepository
from repositories.vehicle_repository import VehicleRepository
from services.availability import (
    _calcular_ocupacion_maxima_simultanea,
    obtener_fechas_deshabilitadas,
    obtener_horas_deshabilitadas,
    obtener_horas_deshabilitadas_con_reservas,
    verificar_disponibilidad,
)
from services.billing_service import BillingService
from services.branch_service import BranchService
from services.notification_service import NotificationService
from services.payments import ReservationPaymentsMixin
from services.time_service import TimeService

logger = get_logger("ReservationService")

# --- SERVICIO DE GESTION DE RESERVAS ---


class ReservationService(ReservationPaymentsMixin):

    @staticmethod
    def create_reservation(db: Session, data: schemas.AdminReservationCreate) -> models.Reservation:
        """CREA UNA NUEVA RESERVA MANUAL DESDE EL PANEL ADMINISTRATIVO."""
        vehiculo = VehicleRepository.get_by_patente(db, data.patente)
        tipo_vehiculo = getattr(data, "tipo_vehiculo", None) or (vehiculo.tipo if vehiculo else VehicleType.AUTO)
        tipo_v_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, "value") else str(tipo_vehiculo)

        monto = BillingService.calculate_total_amount(
            db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin, 
            sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_vehiculo
        )

        info_sede = BranchService.get_branch_info_str(db, data.sucursal_nombre)

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
            cliente_nombre=data.cliente_nombre,
            tipo_vehiculo=tipo_v_str,
            origen="manual"
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        try:
            from services.notification_service import NotificationService
            NotificationService.notify_occupancy_change(db, new_res.sucursal_nombre)
        except Exception:
            logger.warning(f"[RESERVATION] Error notificando cambio de ocupación al crear reserva #{new_res.id}", exc_info=True)
        return new_res

    @staticmethod
    def cleanup_overdue_reservations(db: Session):
        """CANCELA AUTOMATICAMENTE RESERVAS IMPAGAS CUYO TIEMPO DE INICIO YA PASO CON UN MARGEN DE GRACIA.
        NO CANCELA RESERVAS CUYO VEHICULO YA INGRESO AL PREDIO."""
        now = TimeService.now()
        grace_cutoff = now - datetime.timedelta(hours=2)
        cutoff_str = grace_cutoff.strftime("%Y-%m-%d %H:%M")
        
        overdue = ReservationRepository.get_unpaid_overdue(db, cutoff_str)
        
        if overdue:
            logger.info(f"Cancelando {len(overdue)} reservas impagas vencidas. Cutoff: {cutoff_str}")
            # BATCH: una sola query con todos los ids (rutas A5) en vez de 1 query por reserva
            ingresaron = AccessRepository.get_reserva_ids_with_entry(db, [r.id for r in overdue])
            for r in overdue:
                # SI EL VEHICULO YA INGRESO AL PREDIO CON SU RESERVA, NO CANCELAR
                if r.id in ingresaron:
                    continue
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
        vencidas = ReservationRepository.get_expired(db, now_str)
        
        if vencidas:
            logger.info(f"Finalizando {len(vencidas)} reservas vencidas.")
            for r in vencidas:
                r.estado_reserva = ReservationStatus.COMPLETADA
            db.commit()
            # NOTIFICAR A LOS DASHBOARDS PARA QUE REFLEJEN LA DEUDA ACUMULADA TRAS EL VENCIMIENTO
            try:
                from services.notification_service import NotificationService
                sucursales = {_normalizar_sucursal(r.sucursal_nombre) for r in vencidas if r.sucursal_nombre}
                for s in sucursales:
                    NotificationService.notify_occupancy_change(db=db, sucursal_norm=s)
            except Exception as e:
                logger.error(f"Error notificando vencimiento de reservas: {e}")
            return len(vencidas)
        return 0

    @staticmethod
    def get_en_predio_ids(db: Session, reserva_ids) -> set:
        """DEVUELVE LOS IDS DE RESERVAS CUYO ULTIMO EVENTO FISICO FUE UN INGRESO (VEHICULO DENTRO DEL PREDIO)."""
        return AccessRepository.get_en_predio_ids(db, reserva_ids)

    # -------------------------------------------------------------------
    # RUTAS DELGADAS: helpers y wrappers completos para routes/admin y routes/user
    # -------------------------------------------------------------------

    @staticmethod
    def get_reservation_or_404(db: Session, res_id: int, user_id: int = None):
        """Obtiene una reserva o lanza 404. Con user_id, la filtra por dueño."""
        res = ReservationRepository.get_by_id(db, res_id, user_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        return res

    @staticmethod
    def get_permissioned_reservation(db: Session, staff, res_id: int):
        """Obtiene una reserva validando que el operador tenga acceso (admin == todas)."""
        res = ReservationService.get_reservation_or_404(db, res_id)
        if staff.rol != UserRole.ADMIN and res.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        return res

    @staticmethod
    def lookup_patente(db: Session, patente: str) -> dict:
        norm = re.sub(r'[^A-Z0-9]', '', (patente or '').upper())
        if len(norm) < 4:
            return {"encontrado": False, "patente": patente}
        vehicle = VehicleRepository.get_by_normalized_patente_with_active_owner(db, norm)
        if not vehicle or not vehicle.owner:
            return {"encontrado": False, "patente": patente}
        owner = vehicle.owner
        return {
            "encontrado": True, "user_id": owner.id, "nombre": owner.nombre,
            "apellido": owner.apellido, "email": owner.email,
            "tipo_vehiculo": vehicle.tipo or "Auto",
            "marca_modelo": vehicle.marca_modelo or ""
        }

    @staticmethod
    def get_new_reservations_count(db: Session, staff, since_id: int = None) -> dict:
        staff_sucursal = staff.sucursal if staff.rol != UserRole.ADMIN else None
        latest_id, count = ReservationRepository.latest_id_and_count(db, since_id, staff_sucursal)
        return {"count": count, "latest_id": latest_id}

    @staticmethod
    def validar_horario_sucursal(db: Session, sucursal_nombre: str, start: datetime.datetime, end: datetime.datetime):
        if not sucursal_nombre:
            return
        branch = BranchRepository.get_by_name(db, sucursal_nombre)
        if not branch or branch.is_24h or not branch.horario:
            return
        match = re.match(r'^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$', branch.horario.upper().strip())
        if not match:
            return
        open_h, open_m = int(match.group(1)), int(match.group(2))
        close_h, close_m = int(match.group(3)), int(match.group(4))
        if close_h == 0 and close_m == 0:
            close_h, close_m = 23, 59
        apertura = datetime.time(open_h, open_m)
        cierre = datetime.time(close_h, close_m)
        if start.date() != end.date():
            raise HTTPException(status_code=400, detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La estadía no puede extenderse más allá del cierre.")
        if start.time() < apertura or start.time() >= cierre:
            raise HTTPException(status_code=400, detail=f"La sucursal abre de {branch.horario}. La hora de inicio debe estar dentro del horario de atención.")
        if end.time() > cierre:
            raise HTTPException(status_code=400, detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La hora de fin no puede exceder el horario de cierre.")

    @staticmethod
    def validate_manual_vinculacion(db: Session, user_id: int, patente: str):
        user = None
        vehicle = None
        if user_id:
            user = UserRepository.get_active_by_id(db, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            vehicle = VehicleRepository.get_by_user_and_normalized_patente(db, user_id, re.sub(r'[^A-Z0-9]', '', patente.upper()))
            if not vehicle:
                raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")
        return user, vehicle

    @classmethod
    def create_user_reservation(cls, db: Session, user, data: schemas.UserReservationCreate) -> dict:
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
        vehicle = VehicleRepository.get_by_patente_and_user(db, data.patente, user.id)
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a su cuenta")
        p_clean = data.patente.upper().replace(' ', '')
        # LIMITACION: maximo 5 reservas activas o pendientes por usuario
        from models.reservation import Reservation
        from models.enums import ReservationStatus
        activas = db.query(Reservation).filter(Reservation.user_id==user.id, Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA])).count()
        if activas >= 5:
            raise HTTPException(status_code=400, detail="MAXIMO DE RESERVAS PERMITIDAS POR USUARIO ES DE 5")

        existing_overlap = ReservationRepository.get_overlap_by_patente(db, p_clean, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin)
        if existing_overlap:
            raise HTTPException(status_code=400, detail=f"El vehículo patente {data.patente} ya posee otra reserva en la sucursal {data.sucursal_nombre} en el período solicitado.")
        rate = BillingService.get_rate(db, data.tipo_estadia, sucursal=data.sucursal_nombre, tipo_vehiculo=vehicle.tipo)
        start = datetime.datetime.fromisoformat(data.fecha_inicio)
        end = datetime.datetime.fromisoformat(data.fecha_fin)
        max_future = datetime.datetime.now() + datetime.timedelta(days=90)
        if start > max_future:
            raise HTTPException(status_code=400, detail="No se pueden reservar con más de 3 meses de anticipación.")
        if data.tipo_estadia == "hora":
            min_antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS // 60
            if (start - datetime.datetime.now()).total_seconds() < settings.RESERVA_HORA_MIN_SEGUNDOS:
                raise HTTPException(status_code=400, detail=f"Las reservas por hora deben realizarse con al menos {min_antelacion_min} minutos de anticipación.")
            cls.validar_horario_sucursal(db, data.sucursal_nombre, start, end)
        disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo=vehicle.tipo)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        duration_hours = (end - start).total_seconds() / 3600
        if duration_hours <= 0:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")
        if data.tipo_estadia == "dia" and data.dias_semana:
            dias_seleccionados = [int(d.strip()) for d in data.dias_semana.split(",") if d.strip()]
            count, d = 0, start
            while d <= end:
                if d.weekday() in dias_seleccionados:
                    count += 1
                d += datetime.timedelta(days=1)
            if count == 0:
                raise HTTPException(status_code=400, detail="No hay días seleccionados dentro del rango")
            monto = count * rate
        elif data.tipo_estadia == "hora":
            v_str = vehicle.tipo.value if hasattr(vehicle.tipo, "value") else str(vehicle.tipo)
            tarifa_30min = BillingService.get_30min_rate(db, sucursal=data.sucursal_nombre, tipo_vehiculo=v_str)
            monto = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
        elif data.tipo_estadia == "dia":
            monto = max(1, math.ceil(duration_hours / 24)) * rate
        elif data.tipo_estadia == "semana":
            monto = math.ceil(duration_hours / (24 * 7)) * rate
        elif data.tipo_estadia == "quincena":
            monto = math.ceil(duration_hours / (24 * 15)) * rate
        elif data.tipo_estadia == "mes":
            monto = math.ceil(duration_hours / (24 * 30)) * rate
        else:
            monto = math.ceil(duration_hours) * rate
        estado_pago = PaymentStatus.PENDIENTE
        info_sede = BranchService.get_branch_info_str(db, data.sucursal_nombre)
        tipo_v_str = vehicle.tipo.value if hasattr(vehicle.tipo, "value") else str(vehicle.tipo)
        new_res = models.Reservation(
            user_id=user.id, patente=data.patente, fecha_inicio=data.fecha_inicio, fecha_fin=data.fecha_fin,
            tipo_estadia=data.tipo_estadia, monto_total=monto, estado_pago=estado_pago, estado_reserva=ReservationStatus.PENDIENTE,
            sucursal_nombre=data.sucursal_nombre, sucursal_info=info_sede,
            dias_semana=data.dias_semana, tipo_vehiculo=tipo_v_str
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        try:
            NotificationService.notify_occupancy_change(db, new_res.sucursal_nombre)
        except Exception as e:
            logger.error(f"Error notificando nueva reserva: {e}")
        return {"status": "ok", "monto": monto, "estado_pago": estado_pago}

    @classmethod
    def modify_user_reservation(cls, db: Session, user, res_id: int, data: schemas.ReservationUpdate) -> dict:
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
        res = ReservationRepository.get_by_user_and_id(db, user.id, res_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if res.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
            raise HTTPException(status_code=400, detail=f"No se puede modificar una reserva en estado '{res.estado_reserva}'.")
        tipo_efectivo = data.tipo_estadia if data.tipo_estadia else res.tipo_estadia
        suc_efectivo = data.sucursal_nombre if data.sucursal_nombre else res.sucursal_nombre
        start_efectivo = datetime.datetime.fromisoformat(data.fecha_inicio) if data.fecha_inicio else datetime.datetime.fromisoformat(res.fecha_inicio)
        end_efectivo = datetime.datetime.fromisoformat(data.fecha_fin) if data.fecha_fin else datetime.datetime.fromisoformat(res.fecha_fin)
        max_future = datetime.datetime.now() + datetime.timedelta(days=90)
        if start_efectivo > max_future:
            raise HTTPException(status_code=400, detail="No se pueden reservar con más de 3 meses de anticipación.")
        if tipo_efectivo == "hora":
            min_antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS // 60
            if (start_efectivo - datetime.datetime.now()).total_seconds() < settings.RESERVA_HORA_MIN_SEGUNDOS:
                raise HTTPException(status_code=400, detail=f"No se puede modificar una reserva por hora con menos de {min_antelacion_min} minutos de antelación")
            cls.validar_horario_sucursal(db, suc_efectivo, start_efectivo, end_efectivo)
        fec_ini = data.fecha_inicio if data.fecha_inicio else res.fecha_inicio
        fec_fin = data.fecha_fin if data.fecha_fin else res.fecha_fin
        suc_efect = data.sucursal_nombre if data.sucursal_nombre else res.sucursal_nombre
        disp = verificar_disponibilidad(db, suc_efect, fec_ini, fec_fin, exclude_id=res.id)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        monto_anterior, ya_pagado = res.monto_total, res.estado_pago == PaymentStatus.PAGADO
        if data.fecha_inicio:
            res.fecha_inicio = data.fecha_inicio
        if data.fecha_fin:
            res.fecha_fin = data.fecha_fin
        if data.patente:
            if not VehicleRepository.get_by_patente_and_user(db, data.patente, user.id):
                raise HTTPException(status_code=400, detail="Patente no vinculada")
            res.patente = data.patente
        if data.tipo_estadia:
            res.tipo_estadia = data.tipo_estadia
        if data.sucursal_nombre:
            res.sucursal_nombre = data.sucursal_nombre
        vehiculo_mod = VehicleRepository.get_by_patente(db, res.patente)
        tipo_vehiculo_mod = vehiculo_mod.tipo if vehiculo_mod else "Auto"
        rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
        duration_hours = (datetime.datetime.fromisoformat(res.fecha_fin) - datetime.datetime.fromisoformat(res.fecha_inicio)).total_seconds() / 3600
        if duration_hours <= 0:
            raise HTTPException(status_code=400, detail="Fechas inválidas")
        monto_nuevo = math.ceil(duration_hours) * rate
        if res.tipo_estadia == "hora":
            tarifa_30min = BillingService.get_30min_rate(db, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
            monto_nuevo = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
        elif res.tipo_estadia == "dia":
            monto_nuevo = max(1, math.ceil(duration_hours / 24)) * rate
        elif res.tipo_estadia == "semana":
            monto_nuevo = math.ceil(duration_hours / (24 * 7)) * rate
        elif res.tipo_estadia == "quincena":
            monto_nuevo = math.ceil(duration_hours / (24 * 15)) * rate
        elif res.tipo_estadia == "mes":
            monto_nuevo = math.ceil(duration_hours / (24 * 30)) * rate
        if ya_pagado:
            diferencia = monto_nuevo - monto_anterior
            dif_puntos = BillingService.calculate_points(monto_nuevo) - BillingService.calculate_points(monto_anterior)
            if dif_puntos != 0:
                user.puntos_acumulados += dif_puntos
                db.add(models.PointsLog(user_id=user.id, cantidad=dif_puntos, motivo=f"Ajuste Reserva: {res.patente}", fecha=datetime.datetime.now().isoformat()))
            if diferencia > 0:
                if user.saldo < diferencia:
                    raise HTTPException(status_code=400, detail=f"Saldo insuficiente (+${diferencia})")
                user.saldo -= diferencia
            else:
                user.saldo += abs(diferencia)
        else:
            res.estado_pago = PaymentStatus.PENDIENTE
        res.monto_total = monto_nuevo
        db.commit()
        try:
            from services.user_notification_service import UserNotificationService
            msg_detalle = f"Tu reserva #{res.id} ({res.patente}) en {res.sucursal_nombre} fue modificada exitosamente."
            if ya_pagado and diferencia != 0:
                if diferencia > 0:
                    msg_detalle += f" Se debitó una diferencia de ${diferencia:,.2f} de tu saldo."
                else:
                    msg_detalle += f" Se acreditó un reembolso de ${abs(diferencia):,.2f} a tu saldo."
            UserNotificationService.create_notification(
                db, user_id=user.id,
                tipo=models.NotificationType.RESERVATION_MODIFIED,
                titulo="Reserva modificada",
                mensaje=msg_detalle,
                reserva_id=res.id
            )
        except Exception as e:
            logger.error(f"Error creando notificación de reserva modificada: {e}")
        return {"status": "ok", "monto_total": monto_nuevo, "estado_pago": res.estado_pago}

    @staticmethod
    def list_user_reservations(db: Session, user_id: int):
        ReservationService.cleanup_overdue_reservations(db)
        ReservationService.auto_finalize_reservations(db, user_id)
        reservations = ReservationRepository.get_all_by_user(db, user_id)
        en_predio = ReservationService.get_en_predio_ids(db, [r.id for r in reservations])
        updated = False
        for r in reservations:
            r.en_predio = r.id in en_predio
            if not r.sucursal_info or "Sede no especificada" in r.sucursal_info or r.sucursal_info.startswith("Sucursal "):
                info_str = BranchService.get_branch_info_str(db, r.sucursal_nombre)
                if info_str and info_str != "Dirección no disponible":
                    r.sucursal_info = info_str
                    updated = True
        if updated:
            try:
                db.commit()
            except Exception:
                logger.warning("[RESERVATION] Error persistiendo sucursal_info de listado de reservas", exc_info=True)
        return reservations

    @staticmethod
    def confirm_reminder(db: Session, user_id: int, res_id: int) -> dict:
        res = ReservationRepository.get_by_user_and_id(db, user_id, res_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        res.recordatorio_confirmado = True
        from services.user_notification_service import UserNotificationService
        UserNotificationService.mark_reservation_notifications_as_read(db, user_id, res_id, tipo="REMINDER_UNPAID")
        db.commit()
        return {"status": "ok", "message": "Recordatorio confirmado"}

    @staticmethod
    def list_admin_reservations(db: Session, staff, estado: str = None, sucursal: str = None):
        ReservationService.cleanup_overdue_reservations(db)
        staff_sucursal = staff.sucursal if staff.rol != UserRole.ADMIN else None
        results = ReservationRepository.list_filtered(db, estado=estado, sucursal=sucursal, staff_sucursal=staff_sucursal)
        en_predio = ReservationService.get_en_predio_ids(db, [r.id for r in results])
        out = []
        for r in results:
            d = schemas.UserReservationResponse.model_validate(r)
            d.en_predio = r.id in en_predio
            if r.user:
                d.usuario_nombre = r.user.nombre
                d.usuario_apellido = r.user.apellido
                d.user_name = f"{r.user.nombre} {r.user.apellido}"
                d.user_email = r.user.email
            if r.cliente_nombre:
                d.user_name = r.cliente_nombre
                parts = r.cliente_nombre.split(' ', 1)
                d.usuario_nombre = parts[0]
                d.usuario_apellido = parts[1] if len(parts) > 1 else ""
            out.append(d)
        return out

    @staticmethod
    def create_admin_reservation(db: Session, staff, data) -> dict:
        data.patente = format_plate(data.patente)
        if staff.rol != UserRole.ADMIN:
            data.sucursal_nombre = staff.sucursal
        _, vehicle = ReservationService.validate_manual_vinculacion(db, data.user_id, data.patente)
        tipo_v = data.tipo_vehiculo or "Auto"
        if vehicle:
            tipo_v = data.tipo_vehiculo or (vehicle.tipo.value if hasattr(vehicle.tipo, 'value') else str(vehicle.tipo))
        disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo=tipo_v)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        try:
            new_res = ReservationService.create_reservation(db, data)
            if data.pagar:
                result = ReservationService.pay_reservation_manual(db, new_res, data.metodo_pago, data.redemption_ticket_id)
            else:
                result = None
            if new_res.user_id:
                from services.user_notification_service import UserNotificationService
                UserNotificationService.create_notification(
                    db, user_id=new_res.user_id,
                    tipo=models.NotificationType.RESERVATION_CREATED_ADMIN,
                    titulo="Reserva creada por administrador",
                    mensaje=f"Se creó una reserva para {new_res.patente} el {new_res.fecha_inicio} en {new_res.sucursal_nombre}.",
                    reserva_id=new_res.id
                )
            return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total, "pagado": bool(data.pagar),
                    "metodo_pago": data.metodo_pago,
                    "descuento": (result or {}).get("descuento", 0.0),
                    "monto_a_cobrar": (result or {}).get("monto_a_cobrar", new_res.monto_total)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def update_admin_reservation(db: Session, staff, res_id: int, data) -> dict:
        data.patente = format_plate(data.patente)
        reserva = ReservationService.get_reservation_or_404(db, res_id)
        if (getattr(reserva, "origen", None) or "cliente") != "manual":
            raise HTTPException(status_code=400, detail="Solo se pueden editar reservas creadas por administración o empleados")
        if reserva.estado_reserva in (ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA):
            raise HTTPException(status_code=400, detail="No se puede editar una reserva completada o cancelada")
        if staff.rol != UserRole.ADMIN and reserva.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        if staff.rol != UserRole.ADMIN:
            data.sucursal_nombre = staff.sucursal
        if data.fecha_fin <= data.fecha_inicio:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")
        vehicle = None
        if data.user_id:
            _, vehicle = ReservationService.validate_manual_vinculacion(db, data.user_id, data.patente)
        vinculo_final = None
        if data.user_id:
            vinculo_final = data.user_id
        elif reserva.user_id:
            sigue_vinculada = VehicleRepository.get_by_user_and_normalized_patente(
                db, reserva.user_id, re.sub(r'[^A-Z0-9]', '', data.patente.upper())
            )
            vinculo_final = reserva.user_id if sigue_vinculada else None
        tipo_v = data.tipo_vehiculo or (vehicle.tipo if vehicle else "Auto")
        tipo_v_str = tipo_v.value if hasattr(tipo_v, "value") else str(tipo_v)
        disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, exclude_id=res_id, tipo_vehiculo=tipo_v_str)
        if not disp["disponible"]:
            raise HTTPException(status_code=400, detail=disp["mensaje"])
        try:
            monto = BillingService.calculate_total_amount(
                db, data.tipo_estadia, data.fecha_inicio, data.fecha_fin,
                sucursal=data.sucursal_nombre, tipo_vehiculo=tipo_v_str
            )
            ticket_aplicado = None
            if reserva.estado_pago == PaymentStatus.PAGADO:
                ticket_aplicado = RedemptionRepository.get_used_discount_for_reserva(db, reserva.id)
            if ticket_aplicado and ticket_aplicado.valor_descuento:
                porc = ticket_aplicado.valor_descuento
                monto = round(monto * (1 - porc / 100.0), 2)
            monto_anterior = reserva.monto_total or 0.0
            reembolsado_previo = reserva.monto_reembolsado or 0.0
            valor_actual = round(monto_anterior - reembolsado_previo, 2)
            diferencia = round(monto - valor_actual, 2)
            reserva.patente = data.patente
            reserva.fecha_inicio = data.fecha_inicio
            reserva.fecha_fin = data.fecha_fin
            reserva.tipo_estadia = data.tipo_estadia
            reserva.tipo_vehiculo = tipo_v_str
            reserva.sucursal_nombre = data.sucursal_nombre
            reserva.sucursal_info = BranchService.get_branch_info_str(db, data.sucursal_nombre)
            reserva.cliente_nombre = data.cliente_nombre
            reserva.user_id = vinculo_final
            accion = "sin_cambio"
            metodo_ajuste = None
            devolucion_a_saldo = False
            if reserva.estado_pago == PaymentStatus.PAGADO:
                if diferencia > 0:
                    accion = "cobro"
                    metodo_ajuste = data.cobrar_diferencia_metodo
                    reserva.monto_total = round(monto_anterior + diferencia, 2)
                    if metodo_ajuste:
                        reserva.metodo_pago = metodo_ajuste
                    reserva.fecha_pago = datetime.datetime.now().isoformat()
                elif diferencia < 0:
                    accion = "reembolso"
                    metodo_ajuste = data.reembolsar_diferencia_metodo
                    if not metodo_ajuste:
                        metodo_ajuste = reserva.metodo_pago or "Saldo"
                    reembolso = round(abs(diferencia), 2)
                    reserva.monto_reembolsado = round(reembolsado_previo + reembolso, 2)
                    reserva.metodo_pago = metodo_ajuste
                    reserva.fecha_pago = datetime.datetime.now().isoformat()
                    norm_metodo = re.sub(r'[^A-Z]', '', str(metodo_ajuste).upper())
                    devolucion_a_saldo = norm_metodo in ("SALDO", "DIGITAL", "BILLETERA", "BILLETERAAUTOPASS")
                    if devolucion_a_saldo and reserva.user_id and reserva.user:
                        reserva.user.saldo += reembolso
                        puntos_desc = BillingService.calculate_points(reembolso)
                        reserva.user.puntos_acumulados = max(0, reserva.user.puntos_acumulados - puntos_desc)
                        db.add(models.PointsLog(
                            user_id=reserva.user_id, cantidad=-puntos_desc,
                            motivo=f"Reembolso por Edición de Reserva: {reserva.patente}",
                            fecha=datetime.datetime.now().isoformat()
                        ))
                else:
                    reserva.monto_total = monto
            else:
                reserva.monto_total = monto
            if data.metodo_pago and reserva.estado_pago == PaymentStatus.PENDIENTE:
                reserva.metodo_pago = data.metodo_pago
            db.commit()
            db.refresh(reserva)
            if reserva.user_id and reserva.user:
                from services.user_notification_service import UserNotificationService
                if accion == "cobro":
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=f"Tu reserva para {reserva.patente} fue actualizada. Se registró un cobro de ${diferencia:,.2f} por la diferencia ({metodo_ajuste or 'Caja'}).",
                        reserva_id=reserva.id
                    )
                elif accion == "reembolso":
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=(f"Tu reserva para {reserva.patente} fue actualizada. Se te reembolsaron ${abs(diferencia):,.2f} a tu saldo."
                                 if devolucion_a_saldo
                                 else f"Tu reserva para {reserva.patente} fue actualizada. Se te devolvieron ${abs(diferencia):,.2f} en efectivo."),
                        reserva_id=reserva.id
                    )
                else:
                    UserNotificationService.create_notification(
                        db, user_id=reserva.user_id, tipo=models.NotificationType.RESERVATION_MODIFIED,
                        titulo="Reserva modificada por administrador",
                        mensaje=f"Tu reserva para {reserva.patente} fue actualizada: del {reserva.fecha_inicio} al {reserva.fecha_fin} en {reserva.sucursal_nombre}.",
                        reserva_id=reserva.id
                    )
            return {
                "status": "ok", "id": reserva.id, "monto": reserva.monto_total,
                "monto_anterior": monto_anterior, "diferencia": diferencia,
                "accion": accion, "metodo_pago": metodo_ajuste or reserva.metodo_pago,
                "reembolsado_total": reserva.monto_reembolsado or 0.0
            }
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def confirm_reservation_payment(db: Session, staff, res_id: int, data=None) -> dict:
        reserva = ReservationService.get_reservation_or_404(db, res_id)
        if staff.rol != UserRole.ADMIN and reserva.sucursal_nombre != staff.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        metodo = (data.metodo_pago if data else None) or "Caja"
        redemption_ticket_id = (data.redemption_ticket_id if data else None)
        result = ReservationService.pay_reservation_manual(db, reserva, metodo, redemption_ticket_id)
        if reserva.user:
            from services.user_notification_service import UserNotificationService
            UserNotificationService.create_notification(
                db, user_id=reserva.user.id,
                tipo=models.NotificationType.RESERVATION_CONFIRMED,
                titulo="Pago confirmado",
                mensaje=f"El pago de tu reserva #{res_id} ({reserva.patente}) fue confirmado por administrador.",
                reserva_id=res_id
            )
        return {"status": "ok", "message": result["message"], "monto": result["monto"],
                "descuento": result["descuento"], "monto_a_cobrar": result["monto_a_cobrar"]}