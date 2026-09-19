from sqlalchemy.orm import Session
import models
from models.enums import UserRole

#--- REPOSITORIO DE USUARIOS (ACCESO UN DATOS) ---

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> models.User:
        """OBTIENE UN USUARIO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.User).filter(models.User.id == user_id).first()

    @staticmethod
    def get_active_by_id(db: Session, user_id: int) -> models.User:
        """OBTIENE UN USUARIO NO ELIMINADO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()

    @staticmethod
    def get_all_active(db: Session) -> list:
        """OBTIENE TODOS LOS USUARIOS NO ELIMINADOS."""
        return db.query(models.User).filter(models.User.is_deleted == False).all()

    @staticmethod
    def get_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO POR SU DIRECCION DE CORREO ELECTRONICO."""
        return db.query(models.User).filter(models.User.email == email.lower().strip()).first()

    @staticmethod
    def get_active_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO POR SU DIRECCION DE CORREO ELECTRONICO."""
        return db.query(models.User).filter(
            models.User.email == email.lower().strip(), models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_active_by_dni(db: Session, dni: str) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO POR SU DNI."""
        return db.query(models.User).filter(
            models.User.dni == dni, models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_other_by_email(db: Session, email: str, user_id: int) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO CON ESE CORREO, DISTINTO AL INDICADO."""
        return db.query(models.User).filter(
            models.User.email == email.lower().strip(),
            models.User.id != user_id,
            models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_other_by_dni(db: Session, dni: str, user_id: int) -> models.User:
        """BUSCA UN USUARIO NO ELIMINADO CON ESE DNI, DISTINTO AL INDICADO."""
        return db.query(models.User).filter(
            models.User.dni == dni,
            models.User.id != user_id,
            models.User.is_deleted == False
        ).first()

    @staticmethod
    def get_staff(db: Session) -> list:
        """OBTIENE LOS USUARIOS DE STAFF (ADMIN Y LOCAL_ADMIN) NO ELIMINADOS."""
        return db.query(models.User).filter(
            models.User.rol.in_([UserRole.ADMIN, UserRole.LOCAL_ADMIN]),
            models.User.is_deleted == False
        ).all()

    @staticmethod
    def get_by_ids(db: Session, user_ids) -> list:
        """OBTIENE LOS USUARIOS CUYOS IDENTIFICADORES ESTAN EN LA LISTA."""
        if not user_ids:
            return []
        return db.query(models.User).filter(models.User.id.in_(user_ids)).all()

    @staticmethod
    def get_local_admin_by_sucursal(db: Session, sucursal: str) -> models.User:
        """OBTIENE EL LOCAL_ADMIN NO ELIMINADO ASIGNADO A UNA SUCURSAL."""
        return db.query(models.User).filter(
            models.User.sucursal == sucursal,
            models.User.rol == UserRole.LOCAL_ADMIN,
            models.User.is_deleted == False
        ).first()

    @staticmethod
    def update_balance(db: Session, user: models.User, amount: float):
        """ACTUALIZA EL SALDO DE LA CUENTA DE UN USUARIO."""
        user.saldo += amount
        db.commit()

    @staticmethod
    def add_points(db: Session, user: models.User, points: int):
        """INCREMENTA EL PUNTAJE ACUMULADO DE FIDELIZACION."""
        user.puntos_acumulados += points
        db.commit()
