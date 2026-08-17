import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
import schemas

class UserNotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        tipo: str,
        titulo: str,
        mensaje: str,
        reserva_id: Optional[int] = None,
        ticket_id: Optional[int] = None
    ) -> models.UserNotification:
        notif = models.UserNotification(
            user_id=user_id,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            reserva_id=reserva_id,
            ticket_id=ticket_id,
            leido=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[models.UserNotification]:
        return db.query(models.UserNotification)\
            .filter(models.UserNotification.user_id == user_id)\
            .order_by(desc(models.UserNotification.created_at))\
            .offset(offset)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        return db.query(models.UserNotification)\
            .filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == False
            ).count()

    @staticmethod
    def mark_as_read(db: Session, notif_id: int, user_id: int) -> bool:
        notif = db.query(models.UserNotification)\
            .filter(
                models.UserNotification.id == notif_id,
                models.UserNotification.user_id == user_id
            ).first()
        if not notif:
            return False
        notif.leido = True
        db.commit()
        return True

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        count = db.query(models.UserNotification)\
            .filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == False
            ).update({"leido": True})
        db.commit()
        return count

    @staticmethod
    def get_total_count(db: Session, user_id: int) -> int:
        return db.query(models.UserNotification)\
            .filter(models.UserNotification.user_id == user_id).count()

    @staticmethod
    def delete_notification(db: Session, notif_id: int, user_id: int) -> bool:
        notif = db.query(models.UserNotification)\
            .filter(
                models.UserNotification.id == notif_id,
                models.UserNotification.user_id == user_id
            ).first()
        if not notif:
            return False
        db.delete(notif)
        db.commit()
        return True

    @staticmethod
    def clear_read_notifications(db: Session, user_id: int) -> int:
        deleted = db.query(models.UserNotification)\
            .filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == True
            ).delete(synchronize_session=False)
        db.commit()
        return deleted

    @staticmethod
    def mark_reservation_notifications_as_read(db: Session, user_id: int, reserva_id: int, tipo: str = None) -> int:
        """MARCA COMO LEIDAS TODAS LAS NOTIFICACIONES DE UNA RESERVA, OPCIONALMENTE FILTRANDO POR TIPO."""
        q = db.query(models.UserNotification).filter(
            models.UserNotification.user_id == user_id,
            models.UserNotification.reserva_id == reserva_id
        )
        if tipo:
            q = q.filter(models.UserNotification.tipo == tipo)
        count = q.update({"leido": True})
        db.commit()
        return count
