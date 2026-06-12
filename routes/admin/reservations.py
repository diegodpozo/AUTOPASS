import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.reservation_service import ReservationService

router = APIRouter()

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(estado: Optional[str] = Query(None), sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Lista todas las reservas. Los locales solo ven las de su sede."""
    ReservationService.cleanup_overdue_reservations(db)
    
    q = db.query(models.Reservation)

    if estado:
        q = q.filter(models.Reservation.estado_reserva == estado)
    
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
    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == data.user_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    try:
        new_res = ReservationService.create_reservation(db, data)
        return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Confirmación manual de pago."""
    from services.billing_service import BillingService
    from models.enums import PaymentStatus
    
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    if reserva.estado_pago != PaymentStatus.PAGADO:
        reserva.estado_pago = PaymentStatus.PAGADO
        
        # Acreditación de puntos si hay un usuario vinculado
        if reserva.user:
            puntos_ganados = BillingService.calculate_points(reserva.monto_total)
            reserva.user.puntos_acumulados += puntos_ganados
            db.add(models.PointsLog(
                user_id=reserva.user.id,
                cantidad=puntos_ganados,
                motivo=f"Abono Manual Reserva: {reserva.patente}",
                fecha=datetime.datetime.now().isoformat()
            ))

    db.commit()
    return {"status": "ok"}

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Cancelación manual."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        return result
    raise HTTPException(status_code=400, detail=result["message"])

@router.patch("/reservations/{res_id}")
def update_reservation_admin(res_id: int, data: schemas.ReservationUpdate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Permite editar una reserva existente."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")

    updated = ReservationService.update_reservation(db, res_id, data)
    if updated:
        return {"status": "ok", "monto_recalculado": updated.monto_total}
    raise HTTPException(status_code=400, detail="No se pudo actualizar la reserva")
