from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.security import get_current_user
from services.user_service import UserService
from schemas import VehicleCreate

router = APIRouter()

@router.get("/vehicles")
def get_user_vehicles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA TODOS LOS VEHICULOS VINCULADOS A LA CUENTA."""
    return UserService.list_vehicles(db, current_user.id)

@router.post("/vehicles")
def add_user_vehicle(data: VehicleCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """VINCULA UN NUEVO VEHICULO VALIDANDO EL FORMATO DE PATENTE Y EL TIPO."""
    return UserService.add_vehicle(db, current_user, data.patente, data.marca_modelo, data.tipo)

@router.post("/vehicles/{patente}/favorite")
def set_favorite_vehicle(patente: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """MARCA UN VEHICULO COMO FAVORITO (SOLO UNO POR USUARIO). SI YA ESTA MARCADO, LO DESMARCA."""
    return UserService.set_favorite_vehicle(db, current_user, patente)

@router.delete("/vehicles/{patente}")
def delete_user_vehicle(patente: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """DESVINCULA UN VEHICULO DE LA CUENTA DEL USUARIO VALIDANDO RESERVAS Y ESTADIAS ACTIVAS."""
    return UserService.delete_vehicle(db, current_user, patente)
