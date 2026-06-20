from sqlalchemy.orm import Session
from fastapi import HTTPException
import models
import schemas
from core.security import get_password_hash
from models.enums import UserRole

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, sucursal: str = None) -> models.User:
        """CREA UN NUEVO USUARIO EN EL SISTEMA."""
        from routes.parking.utils import normalize_name, normalize_dni
        
        existing = db.query(models.User).filter(models.User.email == user_data.email.lower().strip()).first()
        if existing:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
        new_user = models.User(
            nombre=normalize_name(user_data.nombre),
            apellido=normalize_name(user_data.apellido),
            dni=normalize_dni(user_data.dni),
            telefono=user_data.telefono,
            email=user_data.email.lower().strip(),
            password_hash=get_password_hash(user_data.password),
            rol=rol,
            sucursal=sucursal
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: schemas.UserAdminUpdate) -> models.User:
        """ACTUALIZA LOS DATOS DE UN USUARIO."""
        from routes.parking.utils import normalize_name, normalize_dni
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return None

        if user_data.nombre: user.nombre = normalize_name(user_data.nombre)
        if user_data.apellido: user.apellido = normalize_name(user_data.apellido)
        if user_data.email: user.email = user_data.email.lower().strip()
        if user_data.dni: user.dni = normalize_dni(user_data.dni)
        if user_data.telefono: user.telefono = user_data.telefono
        if user_data.sucursal is not None: user.sucursal = user_data.sucursal
        if user_data.rol: user.rol = user_data.rol

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int):
        """ELIMINA UN USUARIO Y SUS VEHICULOS ASOCIADOS."""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
            
        db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        return True
