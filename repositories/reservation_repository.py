from sqlalchemy.orm import Session
from sqlalchemy import and_
import models
from models.enums import ReservationStatus

#--- REPOSITORIO DE RESERVAS (ACCESO UN DATOS) ---

class ReservationRepository:
    @staticmethod
    def get_by_id(db: Session, res_id: int) -> models.Reservation:
        """BUSCA UNA RESERVA POR SU IDENTIFICADOR UNICO."""
        return db.query(models.Reservation).filter(models.Reservation.id == res_id).first()

    @staticmethod
    def get_by_user_and_id(db: Session, user_id: int, res_id: int) -> models.Reservation:
        """BUSCA UNA RESERVA ESPECIFICA VINCULADA A UN USUARIO DETERMINADO."""
        return db.query(models.Reservation).filter(
            and_(models.Reservation.id == res_id, models.Reservation.user_id == user_id)
        ).first()

    @staticmethod
    def get_past_reservations(db: Session, user_id: int, now_str: str):
        """OBTIENE LAS RESERVAS VENCIDAS QUE AUN NO HAN SIDO COMPLETADAS."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.fecha_fin < now_str
        ).all()

    @staticmethod
    def get_all_by_user(db: Session, user_id: int):
        """RETORNA EL HISTORIAL COMPLETO DE RESERVAS DE UN USUARIO."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id
        ).order_by(models.Reservation.id.desc()).all()

    @staticmethod
    def save(db: Session, reservation: models.Reservation):
        """PERSISTE UNA NUEVA RESERVA O CAMBIOS EN UNA EXISTENTE."""
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation
