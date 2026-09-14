import datetime
import math
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.config import settings
from core.database import get_db
from core.security import get_current_user
from core.logger import get_logger
from services.billing_service import BillingService
from services.branch_service import BranchService
from services.reservation_service import (
    ReservationService,
    verificar_disponibilidad,
    obtener_fechas_deshabilitadas,
    obtener_horas_deshabilitadas_con_reservas
)

logger = get_logger("UserReservations")


def _validar_horario_sucursal(db: Session, sucursal_nombre: str, start: datetime.datetime, end: datetime.datetime):
    """VALIDAR QUE LA RESERVA POR HORA ESTE DENTRO DEL HORARIO DE ATENCION DE LA SUCURSAL."""
    if not sucursal_nombre:
        return

    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    if not branch:
        return
    if branch.is_24h:
        return
    if not branch.horario:
        return

    # FORMATO ESPERADO: "07:00 a 23:00" O "07:00 UN 23:00"
    match = re.match(r'^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$', branch.horario.upper().strip())
    if not match:
        return

    open_h, open_m = int(match.group(1)), int(match.group(2))
    close_h, close_m = int(match.group(3)), int(match.group(4))

    # SI CIERRE ES 00:00 SE TRATA COMO 24:00 (FINAL DEL DIA)
    if close_h == 0 and close_m == 0:
        close_h, close_m = 23, 59

    apertura = datetime.time(open_h, open_m)
    cierre = datetime.time(close_h, close_m)

    start_time = start.time()
    end_time = end.time()

    # RECHAZAR SI LA ESTADIA CRUZA LA MEDIANOCHE (DIA DISTINTO)
    if start.date() != end.date():
        raise HTTPException(
            status_code=400,
            detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La estadía no puede extenderse más allá del cierre."
        )

    if start_time < apertura or start_time >= cierre:
        raise HTTPException(
            status_code=400,
            detail=f"La sucursal abre de {branch.horario}. La hora de inicio debe estar dentro del horario de atención."
        )
    if end_time > cierre:
        raise HTTPException(
            status_code=400,
            detail=f"La sucursal cierra a las {match.group(3)}:{match.group(4)}. La hora de fin no puede exceder el horario de cierre."
        )

router = APIRouter()

@router.get("/reservations/check-availability")
def check_availability(sucursal_nombre: str, fecha_inicio: str, fecha_fin: str, exclude_id: int = None, tipo_vehiculo: str = "Auto", db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """VERIFICA SI HAY LUGARES DISPONIBLES EN LA SUCURSAL PARA EL RANGO SOLICITADO."""
    return verificar_disponibilidad(db, sucursal_nombre, fecha_inicio, fecha_fin, exclude_id, tipo_vehiculo)

@router.get("/reservations/disabled-dates")
def get_disabled_dates(
    sucursal_nombre: str,
    tipo_vehiculo: str = "Auto",
    tipo_estadia: str = "dia",
    fecha_desde: str = None,
    dias: int = 90,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """DEVUELVE LA LISTA DE FECHAS (YYYY-MM-DD) DESHABILITADAS POR CAPACIDAD COMPLETA."""
    fechas = obtener_fechas_deshabilitadas(
        db, sucursal_nombre=sucursal_nombre, tipo_vehiculo=tipo_vehiculo,
        tipo_estadia=tipo_estadia, fecha_desde_str=fecha_desde, dias_evaluar=dias
    )
    return {
        "sucursal_nombre": sucursal_nombre,
        "tipo_vehiculo": tipo_vehiculo,
        "tipo_estadia": tipo_estadia,
        "disabled_dates": fechas
    }

@router.get("/reservations/disabled-hours")
def get_disabled_hours(
    sucursal_nombre: str,
    fecha: str,
    tipo_vehiculo: str = "Auto",
    duracion_horas: float = 1.0,
    paso_minutos: int = 30,
    exclude_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """DEVUELVE LA LISTA DE SLOTS HORARIOS (HH:MM) DESHABILITADOS PARA UN DÍA ESPECÍFICO
    Y LOS RANGOS REALMENTE RESERVADOS PARA DISTINGUIR OCUPACIÓN DE MARGEN DE SOLAPAMIENTO.
    exclude_id: AL EDITAR UNA RESERVA, EXCLUYE SU PROPIO RANGO PARA NO MOSTRARLA COMO OCUPADA."""
    detalle = obtener_horas_deshabilitadas_con_reservas(
        db, sucursal_nombre=sucursal_nombre, fecha_str=fecha,
        tipo_vehiculo=tipo_vehiculo, duracion_horas=duracion_horas,
        paso_minutos=paso_minutos, exclude_id=exclude_id
    )
    return {
        "sucursal_nombre": sucursal_nombre,
        "fecha": fecha,
        "tipo_vehiculo": tipo_vehiculo,
        "disabled_hours": detalle["disabled_hours"],
        "reserved_ranges": detalle["reserved_ranges"]
    }

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def get_user_reservations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA TODAS LAS RESERVAS DEL USUARIO, ACTUALIZANDO ESTADOS AUTOMATICAMENTE."""
    ReservationService.cleanup_overdue_reservations(db)
    ReservationService.auto_finalize_reservations(db, current_user.id)
    reservations = db.query(models.Reservation).filter(models.Reservation.user_id == current_user.id).order_by(models.Reservation.id.desc()).all()
    en_predio = ReservationService.get_en_predio_ids(db, [r.id for r in reservations])
    branches = db.query(models.ParkingBranch).all()
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
            pass
    return reservations

@router.post("/reservations")
def create_user_reservation(res: schemas.UserReservationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CREA UNA NUEVA RESERVA Y PROCESA EL COBRO SI EL SALDO ES SUFICIENTE."""
    from sqlalchemy import func

    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

    # DEBUG LOG: registrar payload entrante para diagnosticar mismatches de sucursal
    try:
        logger.debug(f"RESERVATION CREATE user={getattr(current_user,'id',None)} email={getattr(current_user,'email',None)} payload_sucursal={getattr(res,'sucursal_nombre',None)} payload_patente={getattr(res,'patente',None)}")
    except Exception:
        pass

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == res.patente, models.Vehicle.user_id == current_user.id).first()
    if not vehicle: raise HTTPException(status_code=400, detail="La patente no está vinculada a su cuenta")

    # VALIDAR SUPERPOSICION PARA LA MISMA PATENTE EN LA MISMA SUCURSAL (DOUBLE BOOKING POR VEHICULO)
    # Se permite la misma patente en diferentes sucursales, incluso en el mismo período.
    p_clean = res.patente.upper().replace(' ', '')
    existing_overlap = db.query(models.Reservation).filter(
        func.replace(func.upper(models.Reservation.patente), ' ', '') == p_clean,
        models.Reservation.sucursal_nombre == res.sucursal_nombre,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.estado_pago.in_(["Pendiente", "Pagado"]),
        models.Reservation.fecha_inicio < res.fecha_fin,
        models.Reservation.fecha_fin > res.fecha_inicio
    ).first()
    if existing_overlap:
        raise HTTPException(status_code=400, detail=f"El vehículo patente {res.patente} ya posee otra reserva en la sucursal {res.sucursal_nombre} en el período solicitado.")
    
    rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre, tipo_vehiculo=vehicle.tipo)
    start = datetime.datetime.fromisoformat(res.fecha_inicio)
    end = datetime.datetime.fromisoformat(res.fecha_fin)

    # RECHAZAR RESERVAS CON MAS DE 3 MESES DE ANTICIPACION
    max_future = datetime.datetime.now() + datetime.timedelta(days=90)
    if start > max_future:
        raise HTTPException(status_code=400, detail="No se pueden reservar con más de 3 meses de anticipación.")

    if res.tipo_estadia == "hora":
        min_antelacion_min = settings.RESERVA_HORA_MIN_SEGUNDOS // 60
        if (start - datetime.datetime.now()).total_seconds() < settings.RESERVA_HORA_MIN_SEGUNDOS:
            raise HTTPException(status_code=400, detail=f"Las reservas por hora deben realizarse con al menos {min_antelacion_min} minutos de anticipación.")
        _validar_horario_sucursal(db, res.sucursal_nombre, start, end)

    # VERIFICAR DISPONIBILIDAD
    disp = verificar_disponibilidad(db, res.sucursal_nombre, res.fecha_inicio, res.fecha_fin, tipo_vehiculo=vehicle.tipo)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    duration_hours = (end - start).total_seconds() / 3600

    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")

    if res.tipo_estadia == "dia" and res.dias_semana:
        dias_seleccionados = [int(d.strip()) for d in res.dias_semana.split(",") if d.strip()]
        count, d = 0, start
        while d <= end:
            if d.weekday() in dias_seleccionados: count += 1
            d += datetime.timedelta(days=1)
        if count == 0: raise HTTPException(status_code=400, detail="No hay días seleccionados dentro del rango")
        monto = count * rate
    elif res.tipo_estadia == "hora":
        v_str = vehicle.tipo.value if hasattr(vehicle.tipo, "value") else str(vehicle.tipo)
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=res.sucursal_nombre, tipo_vehiculo=v_str)
        monto = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
    elif res.tipo_estadia == "dia":
        monto = max(1, math.ceil(duration_hours / 24)) * rate
    elif res.tipo_estadia == "semana":
        monto = math.ceil(duration_hours / (24 * 7)) * rate
    elif res.tipo_estadia == "quincena":
        monto = math.ceil(duration_hours / (24 * 15)) * rate
    elif res.tipo_estadia == "mes":
        monto = math.ceil(duration_hours / (24 * 30)) * rate
    else:
        monto = math.ceil(duration_hours) * rate

    estado_pago = "Pendiente"
    info_sede = BranchService.get_branch_info_str(db, res.sucursal_nombre)
    
    new_res = models.Reservation(
        user_id=current_user.id, patente=res.patente, fecha_inicio=res.fecha_inicio, fecha_fin=res.fecha_fin, 
        tipo_estadia=res.tipo_estadia, monto_total=monto, estado_pago=estado_pago, estado_reserva="Pendiente",
        sucursal_nombre=res.sucursal_nombre, sucursal_info=info_sede,
        dias_semana=res.dias_semana
    )
    db.add(new_res)
    db.commit()
    logger.debug(f"POST RESERVE ID={new_res.id} estado_reserva={new_res.estado_reserva}")
    db.refresh(new_res)
    logger.debug(f"POST RESERVE ID={new_res.id} estado_reserva={new_res.estado_reserva}")
    try:
        from services.notification_service import NotificationService
        NotificationService.notify_occupancy_change(db, new_res.sucursal_nombre)
    except Exception as e:
        logger.error(f"Error notificando nueva reserva: {e}")
    return {"status": "ok", "monto": monto, "estado_pago": estado_pago}

@router.patch("/reservations/{res_id}")
def modify_reservation(res_id: int, data: schemas.ReservationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """PERMITE MODIFICAR UNA RESERVA EXISTENTE AJUSTANDO SALDO Y PUNTOS SI CORRESPONDE."""
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

    res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == current_user.id).first()
    if not res: raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if res.estado_reserva in ["Completada", "Cancelada"]:
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
        _validar_horario_sucursal(db, suc_efectivo, start_efectivo, end_efectivo)

    # VERIFICAR DISPONIBILIDAD (EXCLUYENDO LA RESERVA ACTUAL)
    fec_ini = data.fecha_inicio if data.fecha_inicio else res.fecha_inicio
    fec_fin = data.fecha_fin if data.fecha_fin else res.fecha_fin
    suc_efect = data.sucursal_nombre if data.sucursal_nombre else res.sucursal_nombre
    disp = verificar_disponibilidad(db, suc_efect, fec_ini, fec_fin, exclude_id=res.id)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    monto_anterior, ya_pagado = res.monto_total, res.estado_pago == "Pagado"

    if data.fecha_inicio: res.fecha_inicio = data.fecha_inicio
    if data.fecha_fin: res.fecha_fin = data.fecha_fin
    if data.patente: 
        if not db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == current_user.id).first():
            raise HTTPException(status_code=400, detail="Patente no vinculada")
        res.patente = data.patente
    if data.tipo_estadia: res.tipo_estadia = data.tipo_estadia
    if data.sucursal_nombre: res.sucursal_nombre = data.sucursal_nombre

    vehiculo_mod = db.query(models.Vehicle).filter(models.Vehicle.patente == res.patente).first()
    tipo_vehiculo_mod = vehiculo_mod.tipo if vehiculo_mod else "Auto"
    rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
    duration_hours = (datetime.datetime.fromisoformat(res.fecha_fin) - datetime.datetime.fromisoformat(res.fecha_inicio)).total_seconds() / 3600
    if duration_hours <= 0: raise HTTPException(status_code=400, detail="Fechas inválidas")

    monto_nuevo = math.ceil(duration_hours) * rate
    if res.tipo_estadia == "hora":
        tarifa_30min = BillingService.get_30min_rate(db, sucursal=res.sucursal_nombre, tipo_vehiculo=tipo_vehiculo_mod)
        monto_nuevo = max(1, math.ceil(duration_hours * 2)) * tarifa_30min
    elif res.tipo_estadia == "dia": monto_nuevo = max(1, math.ceil(duration_hours / 24)) * rate
    elif res.tipo_estadia == "semana": monto_nuevo = math.ceil(duration_hours / (24 * 7)) * rate
    elif res.tipo_estadia == "quincena": monto_nuevo = math.ceil(duration_hours / (24 * 15)) * rate
    elif res.tipo_estadia == "mes": monto_nuevo = math.ceil(duration_hours / (24 * 30)) * rate

    if ya_pagado:
        diferencia = monto_nuevo - monto_anterior
        dif_puntos = BillingService.calculate_points(monto_nuevo) - BillingService.calculate_points(monto_anterior)
        if dif_puntos != 0:
            current_user.puntos_acumulados += dif_puntos
            db.add(models.PointsLog(user_id=current_user.id, cantidad=dif_puntos, motivo=f"Ajuste Reserva: {res.patente}", fecha=datetime.datetime.now().isoformat()))
        if diferencia > 0:
            if current_user.saldo < diferencia: raise HTTPException(status_code=400, detail=f"Saldo insuficiente (+${diferencia})")
            current_user.saldo -= diferencia
        else: current_user.saldo += abs(diferencia)
    else:
        res.estado_pago = "Pendiente"

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
            db, user_id=current_user.id,
            tipo=models.NotificationType.RESERVATION_MODIFIED,
            titulo="Reserva modificada",
            mensaje=msg_detalle,
            reserva_id=res.id
        )
    except Exception as e:
        logger.error(f"Error creando notificación de reserva modificada: {e}")

    return {"status": "ok", "monto_total": monto_nuevo, "estado_pago": res.estado_pago}

@router.post("/reservations/{res_id}/pay")
def pay_reservation(res_id: int, redemption_ticket_id: int = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """ABONA UNA RESERVA PENDIENTE CON EL SALDO DE LA CUENTA.
    Opcionalmente aplica un descuento (%) de un canje previo (redemption_ticket_id)."""
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
    return ReservationService.pay_reservation(db, current_user, res_id, redemption_ticket_id)

@router.post("/reservations/{res_id}/confirm-reminder")
def confirm_reservation_reminder(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CONFIRMA EL RECORDATORIO DE UNA RESERVA, DETIENE AVISOS Y PREPARA AUTO-CANCELACION."""
    res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    res.recordatorio_confirmado = True
    UserNotificationService.mark_reservation_notifications_as_read(db, current_user.id, res_id, tipo="REMINDER_UNPAID")
    db.commit()
    return {"status": "ok", "message": "Recordatorio confirmado"}

@router.get("/reservations/{res_id}/cancel-simulation")
def simulate_reservation_cancel(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """SIMULA LA CANCELACION PARA PREVISUALIZAR EL MONTO DE REEMBOLSO."""
    res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == current_user.id).first()
    if not res: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    return ReservationService.simulate_refund(db, res)

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CANCELA UNA RESERVA Y REEMBOLSA EL MONTO SI YA FUE PAGADA."""
    return ReservationService.cancel_reservation(db, current_user, res_id)
