import datetime
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user

router = APIRouter()

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Lista todas las reservas. Los locales solo ven las de su sede."""
    from services.reservation_service import ReservationService
    ReservationService.cleanup_overdue_reservations(db)
    
    q = db.query(models.Reservation)
    
    if staff.rol != "admin":
        sucursal = staff.sucursal
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
    elif sucursal:
        q = q.filter(models.Reservation.sucursal_nombre == sucursal)
        
    results = q.order_by(models.Reservation.id.desc()).all()
    
    out = []
    for r in results:
        d = schemas.UserReservationResponse.model_validate(r)
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

@router.post("/reservations")
def create_admin_reservation(data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Permite al administrador o empleado crear una reserva manual."""
    from services.billing_service import BillingService

    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == data.user_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    start = datetime.datetime.fromisoformat(data.fecha_inicio)
    end = datetime.datetime.fromisoformat(data.fecha_fin)
    duration_hours = (end - start).total_seconds() / 3600
    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")

    rate = BillingService.get_rate(db, data.tipo_estadia, sucursal=data.sucursal_nombre)
    if data.tipo_estadia == "hora":
        monto = math.ceil(duration_hours) * rate
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

    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == data.sucursal_nombre).first()
    if branch:
        horario_str = "Abierto 24hs" if branch.is_24h else branch.horario
        info_sede = f"{branch.direccion}. {horario_str}."
    else:
        info_sede = "Sede no especificada."

    new_res = models.Reservation(
        user_id=data.user_id,
        patente=data.patente,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        monto_total=monto,
        estado_pago="Pendiente",
        estado_reserva="Pendiente",
        tipo_estadia=data.tipo_estadia,
        sucursal_nombre=data.sucursal_nombre,
        sucursal_info=info_sede,
        cliente_nombre=data.cliente_nombre
    )
    db.add(new_res)
    db.commit()
    return {"status": "ok", "id": new_res.id, "monto": monto}

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Confirmación manual de pago."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    reserva.estado_pago = "Pagado"
    db.commit()
    return {"status": "ok"}

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Cancelación manual."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        
    from services.reservation_service import ReservationService
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        return result
    raise HTTPException(status_code=400, detail=result["message"])
