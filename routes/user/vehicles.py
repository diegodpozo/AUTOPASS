from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_current_user

router = APIRouter()

@router.get("/vehicles")
def get_user_vehicles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Lista todos los vehículos vinculados a la cuenta."""
    return db.query(models.Vehicle).filter(models.Vehicle.user_id == current_user.id).all()

@router.post("/vehicles")
def add_user_vehicle(patente: str, marca_modelo: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Vincula un nuevo vehículo validando el formato de patente argentina/mercosur."""
    import re
    from routes.parking import normalize_plate, format_plate, normalize_name
    
    p_clean = normalize_plate(patente)
    old_format = re.match(r'^[A-Z]{3}[0-9]{3}$', p_clean)
    new_format = re.match(r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$', p_clean)
    
    if not old_format and not new_format:
        raise HTTPException(status_code=400, detail="Formato de patente inválido. Formatos permitidos: ABC 123 o AB 123 CD")
    
    existing = db.query(models.Vehicle).filter(func.replace(models.Vehicle.patente, ' ', '') == p_clean).first()
    if existing: raise HTTPException(status_code=400, detail="Esta patente ya se encuentra registrada en el sistema")
    
    new_vehicle = models.Vehicle(user_id=current_user.id, patente=format_plate(patente), marca_modelo=normalize_name(marca_modelo))
    db.add(new_vehicle)
    db.commit()
    return {"status": "ok"}

@router.delete("/vehicles/{patente}")
def delete_user_vehicle(patente: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Desvincula un vehículo de la cuenta del usuario."""
    from routes.parking import normalize_plate
    p_clean = normalize_plate(patente)
    vehicle = db.query(models.Vehicle).filter(func.replace(models.Vehicle.patente, ' ', '') == p_clean, models.Vehicle.user_id == current_user.id).first()
    if not vehicle: raise HTTPException(status_code=404, detail="Vehículo no encontrado en su flota")
    
    db.delete(vehicle)
    db.commit()
    return {"status": "ok"}
