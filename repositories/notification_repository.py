from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

import models

#--- REPOSITORIO DE NOTIFICACIONES (ACCESO A DATOS) ---


class NotificationRepository:
    @staticmethod
    def get_by_reserva_and_types(db: Session, reserva_id: int, tipos) -> Optional[models.UserNotification]:
        """OBTIENE LA PRIMERA NOTIFICACION DE UNA RESERVA CUYO TIPO ESTA EN LA LISTA."""
        return db.query(models.UserNotification).filter(
            models.UserNotification.reserva_id == reserva_id,
            models.UserNotification.tipo.in_(tipos)
        ).first()

    @staticmethod
    def save(db: Session, notif: models.UserNotification) -> models.UserNotification:
        """PERSISTE UNA NOTIFICACION NUEVA O CAMBIOS EN UNA EXISTENTE."""
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
        """OBTIENE LAS NOTIFICACIONES DE UN USUARIO ORDENADAS POR FECHA DESCENDENTE."""
        return (
            db.query(models.UserNotification)
            .filter(models.UserNotification.user_id == user_id)
            .order_by(desc(models.UserNotification.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_id_and_user(db: Session, notif_id: int, user_id: int) -> models.UserNotification:
        """OBTIENE UNA NOTIFICACION VINCULADA A UN USUARIO DETERMINADO."""
        return db.query(models.UserNotification).filter(
            models.UserNotification.id == notif_id,
            models.UserNotification.user_id == user_id
        ).first()

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """CUENTA LAS NOTIFICACIONES SIN LEER DE UN USUARIO."""
        return db.query(models.UserNotification).filter(
            models.UserNotification.user_id == user_id,
            models.UserNotification.leido == False
        ).count()

    @staticmethod
    def get_total_count(db: Session, user_id: int) -> int:
        """CUENTA EL TOTAL DE NOTIFICACIONES DE UN USUARIO."""
        return db.query(models.UserNotification).filter(
            models.UserNotification.user_id == user_id
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notif: models.UserNotification) -> None:
        """MARCA UNA NOTIFICACION COMO LEIDA."""
        notif.leido = True
        db.commit()

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """MARCA TODAS LAS NOTIFICACIONES SIN LEER DE UN USUARIO COMO LEIDAS."""
        count = (
            db.query(models.UserNotification)
            .filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == False
            )
            .update({"leido": True}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def mark_reservation_notifications_as_read(
        db: Session,
        user_id: int,
        reserva_id: int,
        tipo: str = None
    ) -> int:
        """MARCA COMO LEIDAS LAS NOTIFICACIONES DE UNA RESERVA, OPCIONALMENTE FILTRANDO POR TIPO."""
        q = db.query(models.UserNotification).filter(
            models.UserNotification.user_id == user_id,
            models.UserNotification.reserva_id == reserva_id
        )
        if tipo:
            q = q.filter(models.UserNotification.tipo == tipo)
        count = q.update({"leido": True}, synchronize_session=False)
        db.commit()
        return count

    @staticmethod
    def mark_ticket_notifications_as_read(db: Session, ticket_ids: List[int]) -> int:
        """MARCA COMO LEIDAS LAS NOTIFICACIONES SIN LEER DE UN CONJUNTO DE TICKETS."""
        if not ticket_ids:
            return 0
        count = (
            db.query(models.UserNotification)
            .filter(
                models.UserNotification.ticket_id.in_(ticket_ids),
                models.UserNotification.leido == False
            )
            .update({"leido": True}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def mark_ticket_read_for_user(db: Session, ticket_id: int, user_id: int) -> int:
        """MARCA COMO LEIDAS LAS NOTIFICACIONES DE UN TICKET PARA UN USUARIO DETERMINADO."""
        count = (
            db.query(models.UserNotification)
            .filter(
                models.UserNotification.ticket_id == ticket_id,
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == False
            )
            .update({"leido": True}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def get_unread_ticket_ids_by_user(db: Session, user_id: int) -> List[int]:
        """TICKETS QUE TIENEN NOTIFICACIONES SIN LEER PARA UN USUARIO."""
        return [
            r[0] for r in db.query(models.UserNotification.ticket_id).filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.ticket_id.isnot(None),
                models.UserNotification.leido == False
            ).all()
        ]

    @staticmethod
    def delete(db: Session, notif: models.UserNotification) -> None:
        """ELIMINA UNA NOTIFICACION."""
        db.delete(notif)
        db.commit()

    @staticmethod
    def clear_read_notifications(db: Session, user_id: int) -> int:
        """ELIMINA TODAS LAS NOTIFICACIONES LEIDAS DE UN USUARIO."""
        deleted = (
            db.query(models.UserNotification)
            .filter(
                models.UserNotification.user_id == user_id,
                models.UserNotification.leido == True
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted