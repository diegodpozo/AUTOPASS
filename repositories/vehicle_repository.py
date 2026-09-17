from sqlalchemy import func
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE VEHICULOS (ACCESO A DATOS) ---


class VehicleRepository:
    @staticmethod
    def get_tipos_by_patentes(db: Session, patentes: list) -> dict:
        """MAPA patente -> tipo de vehiculo PARA LAS PATENTES INDICADAS."""
        rows = db.query(models.Vehicle).filter(models.Vehicle.patente.in_(patentes)).all()
        return {v.patente: v.tipo for v in rows}

    @staticmethod
    def get_by_patente(db: Session, patente: str) -> models.Vehicle:
        """OBTIENE UN VEHICULO POR SU PATENTE EXACTA."""
        return db.query(models.Vehicle).filter(models.Vehicle.patente == patente).first()

    @staticmethod
    def get_by_normalized_patente(db: Session, norm: str) -> models.Vehicle:
        """OBTIENE UN VEHICULO POR PATENTE NORMALIZADA (SIN ESPACIOS, MAYUSCULAS)."""
        return db.query(models.Vehicle).filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == norm
        ).first()

    @staticmethod
    def get_by_patente_and_user(db: Session, patente: str, user_id: int) -> models.Vehicle:
        """OBTIENE UN VEHICULO POR PATENTE EXACTA Y USUARIO DUENO."""
        return db.query(models.Vehicle).filter(
            models.Vehicle.patente == patente,
            models.Vehicle.user_id == user_id
        ).first()

    @staticmethod
    def get_by_user_and_normalized_patente(db: Session, user_id: int, patente_norm: str) -> models.Vehicle:
        """OBTIENE UN VEHICULO DEL USUARIO IGNORANDO ESPACIOS Y MAYUSCULAS EN LA PATENTE."""
        return db.query(models.Vehicle).filter(
            models.Vehicle.user_id == user_id,
            func.replace(func.upper(models.Vehicle.patente), ' ', '') == patente_norm
        ).first()

    @staticmethod
    def get_by_normalized_patente_with_active_owner(db: Session, patente_norm: str) -> models.Vehicle:
        """OBTIENE UN VEHICULO POR PATENTE NORMALIZADA SI SU DUENO NO ESTA ELIMINADO."""
        return (
            db.query(models.Vehicle)
            .join(models.User, models.User.id == models.Vehicle.user_id)
            .filter(
                func.replace(func.upper(models.Vehicle.patente), ' ', '') == patente_norm,
                models.User.is_deleted == False
            )
            .first()
        )