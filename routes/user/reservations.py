from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_current_user
from services.reservation_service import (
    ReservationService,
    verificar_disponibilidad,
    obtener_fechas_deshabilitadas,
    obtener_horas_deshabilitadas_con_reservas
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
    return ReservationService.list_user_reservations(db, current_user.id)

@router.post("/reservations")
def create_user_reservation(res: schemas.UserReservationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CREA UNA NUEVA RESERVA Y PROCESA EL COBRO SI EL SALDO ES SUFICIENTE."""
    return ReservationService.create_user_reservation(db, current_user, res)

@router.patch("/reservations/{res_id}")
def modify_reservation(res_id: int, data: schemas.ReservationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """PERMITE MODIFICAR UNA RESERVA EXISTENTE AJUSTANDO SALDO Y PUNTOS SI CORRESPONDE."""
    return ReservationService.modify_user_reservation(db, current_user, res_id, data)

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
    return ReservationService.confirm_reminder(db, current_user.id, res_id)

@router.get("/reservations/{res_id}/cancel-simulation")
def simulate_reservation_cancel(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """SIMULA LA CANCELACION PARA PREVISUALIZAR EL MONTO DE REEMBOLSO."""
    res = ReservationService.get_reservation_or_404(db, res_id, current_user.id)
    return ReservationService.simulate_refund(db, res)

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation(res_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CANCELA UNA RESERVA Y REEMBOLSA EL MONTO SI YA FUE PAGADA."""
    return ReservationService.cancel_reservation(db, current_user, res_id)