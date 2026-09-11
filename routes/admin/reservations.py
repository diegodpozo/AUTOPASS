import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.reservation_service import ReservationService, verificar_disponibilidad
from services.user_notification_service import UserNotificationService

router = APIRouter()

@router.get("/reservations/patente-lookup")
def patente_lookup(patente: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """BUSCA SI UNA PATENTE ESTA REGISTRADA A UN USUARIO PARA VINCULARLA A UNA RESERVA MANUAL."""
    norm = re.sub(r'[^A-Z0-9]', '', (patente or '').upper())
    if len(norm) < 4:
        return {"encontrado": False, "patente": patente}

    vehicle = (
        db.query(models.Vehicle)
        .join(models.User, models.User.id == models.Vehicle.user_id)
        .filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == norm,
            models.User.is_deleted == False
        )
        .first()
    )
    if not vehicle or not vehicle.owner:
        return {"encontrado": False, "patente": patente}

    owner = vehicle.owner
    return {
        "encontrado": True,
        "user_id": owner.id,
        "nombre": owner.nombre,
        "apellido": owner.apellido,
        "email": owner.email,
        "tipo_vehiculo": vehicle.tipo or "Auto",
        "marca_modelo": vehicle.marca_modelo or ""
    }

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

@router.post("/reservations")
def create_admin_reservation(data: schemas.AdminReservationCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """PERMITE AL ADMINISTRADOR O EMPLEADO CREAR UNA RESERVA MANUAL."""
    if staff.rol != "admin":
        data.sucursal_nombre = staff.sucursal

    vehicle = None
    if data.user_id:
        user = db.query(models.User).filter(models.User.id == data.user_id, models.User.is_deleted == False).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        vehicle = db.query(models.Vehicle).filter(
            models.Vehicle.user_id == data.user_id,
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == re.sub(r'[^A-Z0-9]', '', data.patente.upper())
        ).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="La patente no está vinculada a ese usuario")

    # VERIFICAR DISPONIBILIDAD
    tipo_v = data.tipo_vehiculo or (vehicle.tipo if vehicle else "Auto")
    disp = verificar_disponibilidad(db, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo=tipo_v)
    if not disp["disponible"]:
        raise HTTPException(status_code=400, detail=disp["mensaje"])

    try:
        new_res = ReservationService.create_reservation(db, data)
        if data.pagar:
            ReservationService.pay_reservation_manual(db, new_res, data.metodo_pago)
        if new_res.user_id:
            UserNotificationService.create_notification(
                db, user_id=new_res.user_id,
                tipo="reserva_creada_admin",
                titulo="Reserva creada por administrador",
                mensaje=f"Se creó una reserva para {new_res.patente} el {new_res.fecha_inicio} en {new_res.sucursal_nombre}.",
                reserva_id=new_res.id
            )
        return {"status": "ok", "id": new_res.id, "monto": new_res.monto_total, "pagado": bool(data.pagar), "metodo_pago": data.metodo_pago}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reservations/{res_id}/confirm-payment")
def confirm_reservation_payment(res_id: int, data: schemas.ConfirmPaymentRequest = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CONFIRMACION MANUAL DE PAGO."""
    reserva = db.query(models.Reservation).filter(models.Reservation.id == res_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if staff.rol != "admin" and reserva.sucursal_nombre != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta reserva")
    
    metodo = (data.metodo_pago if data else None) or "Caja"
    result = ReservationService.pay_reservation_manual(db, reserva, metodo)

    if reserva.user:
        UserNotificationService.create_notification(
            db, user_id=reserva.user.id,
            tipo="pago_confirmado_admin",
            titulo="Pago confirmado",
            mensaje=f"El pago de tu reserva #{res_id} ({reserva.patente}) fue confirmado por administrador.",
            reserva_id=res_id
        )

    return {"status": "ok", "message": result["message"]}

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
        if reserva and reserva.user and reserva.estado_reserva == "Cancelada":
            UserNotificationService.create_notification(
                db, user_id=reserva.user.id,
                tipo="reserva_cancelada_admin",
                titulo="Reserva cancelada por administrador",
                mensaje=f"Tu reserva #{res_id} ({reserva.patente}) fue cancelada.",
                reserva_id=res_id
            )
        return result
    raise HTTPException(status_code=400, detail=result["message"])


