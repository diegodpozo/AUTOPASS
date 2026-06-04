from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import get_current_user, get_password_hash, verify_password

router = APIRouter()

@router.get("/me", response_model=schemas.UserBase)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Retorna la información del perfil del usuario autenticado."""
    return current_user

@router.put("/me", response_model=schemas.UserBase)
def update_me(data: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Actualiza los datos personales del usuario."""
    from routes.parking import normalize_name
    if data.nombre: current_user.nombre = normalize_name(data.nombre)
    if data.apellido: current_user.apellido = normalize_name(data.apellido)
    if data.telefono: current_user.telefono = data.telefono
    if data.email: current_user.email = data.email.lower().strip()
    if data.direccion: current_user.direccion = data.direccion
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
def change_password(data: schemas.ChangePassword, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Procesa el cambio de contraseña validando la anterior."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual ingresada es incorrecta")
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"status": "ok", "message": "Contraseña actualizada exitosamente"}
