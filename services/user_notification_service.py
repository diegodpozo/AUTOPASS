from core.time import localnow
from typing import List, Optional
from sqlalchemy.orm import Session
import models
import schemas
from repositories.notification_repository import NotificationRepository

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
            created_at=localnow()
        )
        return NotificationRepository.save(db, notif)

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[models.UserNotification]:
        return NotificationRepository.get_user_notifications(db, user_id, limit=limit, offset=offset)

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        return NotificationRepository.get_unread_count(db, user_id)

    @staticmethod
    def mark_as_read(db: Session, notif_id: int, user_id: int) -> bool:
        notif = NotificationRepository.get_by_id_and_user(db, notif_id, user_id)
        if not notif:
            return False
        NotificationRepository.mark_as_read(db, notif)
        return True

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        return NotificationRepository.mark_all_as_read(db, user_id)

    @staticmethod
    def get_total_count(db: Session, user_id: int) -> int:
        return NotificationRepository.get_total_count(db, user_id)

    @staticmethod
    def delete_notification(db: Session, notif_id: int, user_id: int) -> bool:
        notif = NotificationRepository.get_by_id_and_user(db, notif_id, user_id)
        if not notif:
            return False
        NotificationRepository.delete(db, notif)
        return True

    @staticmethod
    def clear_read_notifications(db: Session, user_id: int) -> int:
        return NotificationRepository.clear_read_notifications(db, user_id)

    @staticmethod
    def mark_reservation_notifications_as_read(db: Session, user_id: int, reserva_id: int, tipo: str = None) -> int:
        """MARCA COMO LEIDAS TODAS LAS NOTIFICACIONES DE UNA RESERVA, OPCIONALMENTE FILTRANDO POR TIPO."""
        return NotificationRepository.mark_reservation_notifications_as_read(db, user_id, reserva_id, tipo)
