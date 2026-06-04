import datetime
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_current_user
from services.billing_service import BillingService
from services.reservation_service import ReservationService

router = APIRouter()

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def get_user_reservations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Lista todas las reservas del usuario, actualizando estados automáticamente."""
    ReservationService.cleanup_overdue_reservations(db)
    ReservationService.auto_finalize_reservations(db, current_user.id)
    return db.query(models.Reservation).filter(models.Reservation.user_id == current_user.id).order_by(models.Reservation.id.desc()).all()

@router.post("/reservations")
def create_user_reservation(res: schemas.UserReservationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Crea una nueva reserva y procesa el cobro si el saldo es suficiente."""
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == res.patente, models.Vehicle.user_id == current_user.id).first()
    if not vehicle: raise HTTPException(status_code=400, detail="La patente no está vinculada a su cuenta")
    
    rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre)
    start = datetime.datetime.fromisoformat(res.fecha_inicio)
    
    if (start - datetime.datetime.now()).total_seconds() < 7200:
        raise HTTPException(status_code=400, detail="Las reservas deben realizarse con al menos 2 horas de anticipación.")

    end = datetime.datetime.fromisoformat(res.fecha_fin)
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
        monto = math.ceil(duration_hours) * rate
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
    
    sucursales_info = {
        "AUTOPASS Central": "Av. del Libertador 1200, CABA. Abierto 24hs.",
        "AUTOPASS Ituzaingó": "Punto de Acceso Estación Ituzaingó. Abierto 24hs.",
        "AUTOPASS Castelar": "Centro Comercial Castelar. Abierto 24hs.",
        "AUTOPASS Morón": "Plaza Oeste Shopping - Morón. Abierto 24hs."
    }
    
    new_res = models.Reservation(
        user_id=current_user.id, patente=res.patente, fecha_inicio=res.fecha_inicio, fecha_fin=res.fecha_fin, 
        tipo_estadia=res.tipo_estadia, monto_total=monto, estado_pago=estado_pago, estado_reserva="Pendiente",
        sucursal_nombre=res.sucursal_nombre, sucursal_info=sucursales_info.get(res.sucursal_nombre, "Sede no especificada."),
        dias_semana=res.dias_semana
    )
    db.add(new_res)
    db.commit()
    return {"status": "ok", "monto": monto, "estado_pago": estado_pago}

@router.patch("/reservations/{res_id}")
def modify_reservation(res_id: int, data: schemas.ReservationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Permite modificar una reserva existente ajustando saldo y puntos si corresponde."""
    res = db.query(models.Reservation).filter(models.Reservation.id == res_id, models.Reservation.user_id == current_user.id).first()
    if not res: raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if (datetime.datetime.fromisoformat(res.fecha_inicio) - datetime.datetime.now()).total_seconds() < 7200:
        raise HTTPException(status_code=400, detail="No se puede modificar con menos de 2 horas de antelación")

    monto_anterior, ya_pagado = res.monto_total, res.estado_pago == "Pagado"

    if data.fecha_inicio: res.fecha_inicio = data.fecha_inicio
    if data.fecha_fin: res.fecha_fin = data.fecha_fin
    if data.patente: 
        if not db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == current_user.id).first():
            raise HTTPException(status_code=400, detail="Patente no vinculada")
        res.patente = data.patente
    if data.tipo_estadia: res.tipo_estadia = data.tipo_estadia
    if data.sucursal_nombre: res.sucursal_nombre = data.sucursal_nombre

    rate = BillingService.get_rate(db, res.tipo_estadia, sucursal=res.sucursal_nombre)
    duration_hours = (datetime.datetime.fromisoformat(res.fecha_fin) - datetime.datetime.fromisoformat(res.fecha_inicio)).total_seconds() / 3600
    if duration_hours <= 0: raise HTTPException(status_code=400, detail="Fechas inválidas")

    monto_nuevo = math.ceil(duration_hours) * rate
    if res.tipo_estadia == "dia": monto_nuevo = max(1, math.ceil(duration_hours / 24)) * rate
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
    return {"status": "ok", "monto_total": monto_nuevo, "estado_pago": res.estado_pago}

@router.post("/reservations/{res_id}/pay")
def pay_reservation(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Abona una reserva pendiente con el saldo de la cuenta."""
    return ReservationService.pay_reservation(db, current_user, res_id)

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Cancela una reserva y reembolsa el monto si ya fue pagada."""
    return ReservationService.cancel_reservation(db, current_user, res_id)
