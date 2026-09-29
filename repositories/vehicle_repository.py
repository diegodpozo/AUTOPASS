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
    def get_by_normalized_patentes(db: Session, normas: list) -> list:
        """OBTIENE TODOS LOS VEHICULOS CUYA PATENTE NORMALIZADA ESTA EN LA LISTA (1 sola query).

        Equivalente batch de get_by_normalized_patente: indispensable porque los logs
        de acceso guardan la patente normalizada ("AB123CD") y el alta de vehiculo la
        guarda con formato visual ("AB 123 CD"), por lo que el match exacto falla.
        """
        if not normas:
            return []
        return db.query(models.Vehicle).filter(
            func.replace(func.upper(models.Vehicle.patente), ' ', '').in_(normas)
        ).all()

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

    @staticmethod
    def get_plates_by_user(db: Session, user_id: int) -> list:
        """PATENTES DE TODOS LOS VEHICULOS DE UN USUARIO."""
        rows = db.query(models.Vehicle.patente).filter(models.Vehicle.user_id == user_id).all()
        return [v.patente for v in rows]

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> list:
        """OBTIENE TODOS LOS VEHICULOS DE UN USUARIO."""
        return db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id).all()

    @staticmethod
    def get_other_by_user(db: Session, user_id: int, vehicle_id: int) -> models.Vehicle:
        """OBTIENE UN VEHICULO DEL USUARIO DISTINTO AL INDICADO."""
        return db.query(models.Vehicle).filter(
            models.Vehicle.user_id == user_id,
            models.Vehicle.id != vehicle_id
        ).first()

    @staticmethod
    def unset_favorite_for_user(db: Session, user_id: int):
        """QUITA EL FAVORITO A TODOS LOS VEHICULOS DE UN USUARIO."""
        db.query(models.Vehicle).filter(
            models.Vehicle.user_id == user_id,
            models.Vehicle.is_favorite == True
        ).update({"is_favorite": False})