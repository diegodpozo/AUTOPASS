from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_current_user

router = APIRouter()

@router.get("/vehicles")
def get_user_vehicles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA TODOS LOS VEHICULOS VINCULADOS A LA CUENTA."""
    return db.query(models.Vehicle).filter(models.Vehicle.user_id == current_user.id).all()

@router.post("/vehicles")
def add_user_vehicle(patente: str, marca_modelo: str, tipo: str = "Auto", db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """VINCULA UN NUEVO VEHICULO VALIDANDO EL FORMATO DE PATENTE ARGENTINA/MERCOSUR."""
    import re
    from routes.parking import normalize_plate, format_plate, normalize_name
    
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

    if tipo not in ["Auto", "Moto", "Camioneta"]:
        raise HTTPException(status_code=400, detail="Tipo de vehículo inválido. Use 'Auto', 'Moto' o 'Camioneta'.")

    p_clean = normalize_plate(patente)
    # PATENTES DE AUTOS / CAMIONETAS (3 LETRAS 3 NUMEROS O 2 LETRAS 3 NUMEROS 2 LETRAS)
    # PATENTES DE MOTOS (1 LETRA 3 NUMEROS 3 LETRAS O SIMILAR)
    old_format = re.match(r'^[A-Z]{3}[0-9]{3}$', p_clean)
    new_format = re.match(r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$', p_clean)
    moto_format = re.match(r'^[0-9]{3}[A-Z]{3}$', p_clean) or re.match(r'^[A-Z]{1}[0-9]{3}[A-Z]{3}$', p_clean)
    
    if not old_format and not new_format and not moto_format:
        raise HTTPException(status_code=400, detail="Formato de patente inválido.")
    
    existing = db.query(models.Vehicle).filter(func.replace(models.Vehicle.patente, ' ', '') == p_clean).first()
    if existing: raise HTTPException(status_code=400, detail="Esta patente ya se encuentra registrada en el sistema")
    
    new_vehicle = models.Vehicle(
        user_id=current_user.id, 
        patente=format_plate(patente), 
        marca_modelo=normalize_name(marca_modelo),
        tipo=tipo
    )
    db.add(new_vehicle)
    db.commit()
    return {"status": "ok"}

@router.post("/vehicles/{patente}/favorite")
def set_favorite_vehicle(patente: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """MARCA UN VEHICULO COMO FAVORITO (SOLO UNO POR USUARIO). SI YA ESTA MARCADO, LO DESMARCA."""
    from routes.parking import normalize_plate
    p_clean = normalize_plate(patente)

    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

    vehicle = db.query(models.Vehicle).filter(
        func.replace(models.Vehicle.patente, ' ', '') == p_clean,
        models.Vehicle.user_id == current_user.id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado en su flota")

    if vehicle.is_favorite:
        # SI YA ERA FAVORITO, LO DESMARCA
        vehicle.is_favorite = False
    else:
        # DESMARCAR CUALQUIER FAVORITO ANTERIOR Y MARCAR EL NUEVO
        db.query(models.Vehicle).filter(
            models.Vehicle.user_id == current_user.id,
            models.Vehicle.is_favorite == True
        ).update({"is_favorite": False})
        vehicle.is_favorite = True

    db.commit()
    return {"status": "ok", "patente": vehicle.patente, "is_favorite": vehicle.is_favorite}

@router.delete("/vehicles/{patente}")
def delete_user_vehicle(patente: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """DESVINCULA UN VEHICULO DE LA CUENTA DEL USUARIO VALIDANDO RESERVAS Y ESTADIAS ACTIVAS."""
    import datetime
    from routes.parking import normalize_plate
    p_clean = normalize_plate(patente)

    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")

    vehicle = db.query(models.Vehicle).filter(
        func.replace(models.Vehicle.patente, ' ', '') == p_clean, 
        models.Vehicle.user_id == current_user.id
    ).first()
    if not vehicle: 
        raise HTTPException(status_code=404, detail="Vehículo no encontrado en su flota")
    
    # 1. VALIDAR RESERVAS ACTIVAS O PENDIENTES
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    active_res = db.query(models.Reservation).filter(
        func.replace(func.upper(models.Reservation.patente), ' ', '') == p_clean,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.fecha_fin >= now_str
    ).first()
    if active_res:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar un vehículo que posee reservas activas o pendientes."
        )

    # 2. VALIDAR SI EL VEHICULO SE ENCUENTRA FISICAMENTE DENTRO DEL ESTACIONAMIENTO
    last_entry = db.query(models.AccessLog).filter(
        func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p_clean,
        models.AccessLog.tipo_evento == "ENTRADA"
    ).order_by(models.AccessLog.id.desc()).first()

    if last_entry:
        subsequent_exit = db.query(models.AccessLog).filter(
            func.replace(func.upper(models.AccessLog.patente_detectada), ' ', '') == p_clean,
            models.AccessLog.tipo_evento == "SALIDA",
            models.AccessLog.id > last_entry.id
        ).first()
        if not subsequent_exit:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar un vehículo que se encuentra físicamente ingresado en el estacionamiento."
            )

    # 3. VALIDAR DEUDAS / ESTADIAS IMPAGAS PENDIENTES
    # SOLO CONSTITUYE DEUDA LA SESION ACTUAL, SI SIGUE ABIERTA Y SIN PAGO CONFIRMADO.
    # REGISTROS HISTORICOS CON SALIDA (CERRADOS O CANCELADOS) NO BLOQUEAN EL BORRADO.
    if last_entry and not last_entry.pago_confirmado and not subsequent_exit:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar un vehículo con deudas o estadías impagas pendientes."
        )

    # REASIGNAR FAVORITO O PATENTE PRINCIPAL SI CORRESPONDE
    if vehicle.is_favorite:
        other = db.query(models.Vehicle).filter(
            models.Vehicle.user_id == current_user.id,
            models.Vehicle.id != vehicle.id
        ).first()
        if other:
            other.is_favorite = True

    if current_user.patente and normalize_plate(current_user.patente) == p_clean:
        other = db.query(models.Vehicle).filter(
            models.Vehicle.user_id == current_user.id,
            models.Vehicle.id != vehicle.id
        ).first()
        current_user.patente = other.patente if other else None

    db.delete(vehicle)
    db.commit()
    return {"status": "ok"}
