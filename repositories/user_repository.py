from sqlalchemy.orm import Session
import models

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
    def get_by_email(db: Session, email: str) -> models.User:
        """BUSCA UN USUARIO POR SU DIRECCION DE CORREO ELECTRONICO."""
        return db.query(models.User).filter(models.User.email == email.lower().strip()).first()

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
