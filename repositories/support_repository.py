from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

import models

#--- REPOSITORIO DE SOPORTE (TICKETS Y MENSAJES) ---


class SupportRepository:
    @staticmethod
    def create_ticket(
        db: Session,
        ticket: models.SupportTicket,
        build_message
    ) -> models.SupportTicket:
        """PERSISTE UN TICKET CON SU PRIMER MENSAJE ASOCIADO.

        `build_message(ticket)` recibe el ticket ya con `id` asignado (tras flush)
        y devuelve el SupportTicketMessage del primer mensaje."""
        db.add(ticket)
        db.flush()
        db.add(build_message(ticket))
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def save_message(db: Session, msg: models.SupportTicketMessage) -> models.SupportTicketMessage:
        """PERSISTE UN MENSAJE NUEVO Y CONFIRMA EL TICKET ASOCIADO."""
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_user_tickets(db: Session, user_id: int) -> List[models.SupportTicket]:
        """OBTIENE LOS TICKETS DE UN USUARIO ORDENADOS POR FECHA DESCENDENTE."""
        return (
            db.query(models.SupportTicket)
            .filter(models.SupportTicket.user_id == user_id)
            .order_by(desc(models.SupportTicket.created_at))
            .all()
        )

    @staticmethod
    def get_all_with_user(db: Session) -> List[models.SupportTicket]:
        """OBTIENE TODOS LOS TICKETS CON SU USUARIO CARGADO, ORDENADOS POR FECHA DESCENDENTE."""
        return (
            db.query(models.SupportTicket)
            .options(joinedload(models.SupportTicket.user))
            .order_by(desc(models.SupportTicket.created_at))
            .all()
        )

    @staticmethod
    def get_all(db: Session) -> List[models.SupportTicket]:
        """OBTIENE TODOS LOS TICKETS."""
        return db.query(models.SupportTicket).all()

    @staticmethod
    def get_by_id(db: Session, ticket_id: int) -> Optional[models.SupportTicket]:
        """OBTIENE UN TICKET POR SU IDENTIFICADOR UNICO."""
        return db.query(models.SupportTicket).filter(
            models.SupportTicket.id == ticket_id
        ).first()

    @staticmethod
    def get_by_id_with_user(db: Session, ticket_id: int) -> Optional[models.SupportTicket]:
        """OBTIENE UN TICKET CON SU USUARIO CARGADO."""
        return db.query(models.SupportTicket).options(
            joinedload(models.SupportTicket.user)
        ).filter(
            models.SupportTicket.id == ticket_id
        ).first()

    @staticmethod
    def get_by_id_and_user(db: Session, ticket_id: int, user_id: int) -> Optional[models.SupportTicket]:
        """OBTIENE UN TICKET VINCULADO A UN USUARIO DETERMINADO."""
        return db.query(models.SupportTicket).filter(
            models.SupportTicket.id == ticket_id,
            models.SupportTicket.user_id == user_id
        ).first()

    @staticmethod
    def get_messages_for_tickets(db: Session, ticket_ids: List[int]) -> List[models.SupportTicketMessage]:
        """OBTIENE LOS MENSAJES DE UN CONJUNTO DE TICKETS CON SU AUTOR CARGADO, ORDENADOS POR FECHA."""
        if not ticket_ids:
            return []
        return (
            db.query(models.SupportTicketMessage)
            .options(joinedload(models.SupportTicketMessage.user))
            .filter(models.SupportTicketMessage.ticket_id.in_(ticket_ids))
            .order_by(models.SupportTicketMessage.created_at)
            .all()
        )

    @staticmethod
    def get_messages_by_ticket(db: Session, ticket_id: int) -> List[models.SupportTicketMessage]:
        """OBTIENE LOS MENSAJES DE UN TICKET ORDENADOS POR FECHA."""
        return (
            db.query(models.SupportTicketMessage)
            .filter(models.SupportTicketMessage.ticket_id == ticket_id)
            .order_by(models.SupportTicketMessage.created_at)
            .all()
        )