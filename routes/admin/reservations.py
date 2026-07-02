import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.reservation_service import ReservationService, verificar_disponibilidad
from services.user_notification_service import UserNotificationService

router = APIRouter()

@router.get("/reservations", response_model=List[schemas.UserReservationResponse])
def list_reservations(estado: Optional[str] = Query(None), sucursal: Optional[str] = Query(None), db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """LISTA TODAS LAS RESERVAS. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
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
    """PERMITE AL ADMINISTRADOR O EMPLEADO CREAR UNA RESERVA MANUAL."""
    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id, models.User.is_deleted == False).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.patente == data.patente, models.Vehicle.user_id == data.user_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    # VERIFICAR DISPONIBILIDAD
    disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    try:
        new_res = ReservationService.create_reservation(db, data)
        if new_res.user_id:
            UserNotificationService.create_notification(
                db, user_id=new_res.user_id,
                tipo="reserva_creada_admin",
                titulo="Reserva creada por administrador",
                mensaje=f"Se creó una reserva para {new_res.patente} el {new_res.fecha_inicio} en {new_res.sucursal_nombre}.",
                reserva_id=new_res.id
            )
        return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CONFIRMACION MANUAL DE PAGO."""
    from services.billing_service import BillingService
    from models.enums import PaymentStatus
    
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    if reserva.estado_pago != PaymentStatus.PAGADO:
        reserva.estado_pago = PaymentStatus.PAGADO
        
        # ACREDITACION DE PUNTOS SI HAY UN USUARIO VINCULADO
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

    if reserva.user:
        UserNotificationService.create_notification(
            db, user_id=reserva.user.id,
            tipo="pago_confirmado_admin",
            titulo="Pago confirmado",
            mensaje=f"El pago de tu reserva #{res_id} ({reserva.patente}) fue confirmado por administrador.",
            reserva_id=res_id
        )

    return {"status": "ok"}

@router.post("/reservations/{res_id}/cancel")
def cancel_reservation_admin(res_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CANCELACION MANUAL."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva: raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
        
    result = ReservationService.cancel_reservation(db, None, res_id)
    if result["status"] == "ok":
        reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
        if reserva and reserva.user:
            UserNotificationService.create_notification(
                db, user_id=reserva.user.id,
                tipo="reserva_cancelada_admin",
                titulo="Reserva cancelada por administrador",
                mensaje=f"Tu reserva #{res_id} ({reserva.patente}) fue cancelada.",
                reserva_id=res_id
            )
        return result
    raise HTTPException(status_code=400, detail=result["message"])

@router.patch("/reservations/{res_id}")
def update_reservation_admin(res_id: int, data: schemas.ReservationUpdate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PERMITE EDITAR UNA RESERVA EXISTENTE."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")

    # VERIFICAR DISPONIBILIDAD (EXCLUYENDO LA RESERVA ACTUAL)
    fec_ini = data.fecha_inicio if data.fecha_inicio else reserva.fecha_inicio
    fec_fin = data.fecha_fin if data.fecha_fin else reserva.fecha_fin
    suc_efect = data.sucursal_nombre if data.sucursal_nombre else reserva.sucursal_nombre
    disp = verificar_disponibilidad(db, suc_efect, fec_ini, fec_fin, exclude_id=res_id)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    updated = ReservationService.update_reservation(db, res_id, data)
    if updated:
        if updated.user_id:
            UserNotificationService.create_notification(
                db, user_id=updated.user_id,
                tipo="reserva_modificada_admin",
                titulo="Reserva modificada por administrador",
                mensaje=f"Tu reserva #{res_id} ({updated.patente}) fue modificada. Monto recalculado: ${updated.monto_total}.",
                reserva_id=res_id
            )
        return {"status": "ok", "monto_recalculado": updated.monto_total}
    raise HTTPException(status_code=400, detail="No se pudo actualizar la reserva")
