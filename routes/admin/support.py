from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from core.database import get_db
from core.limiter import admin_rate_limit
from core.security import get_operational_user
from services.support_service import SupportService
from repositories.notification_repository import NotificationRepository
from repositories.support_repository import SupportRepository
from services.notification_service import NotificationService

router = APIRouter()

@router.get("/support-tickets/pending-count")
def get_admin_support_pending_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """RETORNA LA CANTIDAD DE TICKETS DE SOPORTE PENDIENTES (NO RESUELTOS)
    QUE PUEDE VER EL ADMIN ACTUAL. Alimenta la burbuja de 'Soporte & Tickets'."""
    count = SupportService.get_admin_pending_count(db, current_user)
    return {"count": count}

@router.patch("/support-tickets/{ticket_id}/read-notifs", dependencies=[Depends(admin_rate_limit)])
def mark_ticket_notifications_read(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """MARCA COMO LEIDAS LAS NOTIFICACIONES DE UN TICKET PARA EL ADMIN ACTUAL."""
    updated = NotificationRepository.mark_ticket_read_for_user(db, ticket_id, current_user.id)
    return {"marked": updated}

@router.get("/support-tickets/{ticket_id}")
def get_admin_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """RETORNA UN TICKET ESPECIFICO CON TODOS SUS MENSAJES."""
    ticket = SupportRepository.get_by_id_with_user(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    messages = SupportService.get_ticket_messages(db, ticket_id)
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "cliente_nombre": f"{ticket.user.nombre} {ticket.user.apellido}".strip() if ticket.user else "Cliente Eliminado",
        "cliente_email": ticket.user.email if ticket.user else "N/A",
        "categoria": ticket.categoria,
        "sucursal": ticket.sucursal,
        "asunto": ticket.asunto,
        "mensaje": ticket.mensaje,
        "estado": ticket.estado,
        "respuesta": ticket.respuesta,
        "messages": messages,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }

@router.get("/support-tickets")
def get_admin_support_tickets(
    sucursal: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """RETORNA TODOS LOS TICKETS DE SOPORTE FILTRADOS SEGUN ROL Y PARAMETROS."""
    return SupportService.get_admin_tickets(db, current_user, sucursal_filter=sucursal, estado_filter=estado)

@router.patch("/support-tickets/{ticket_id}", dependencies=[Depends(admin_rate_limit)])
def update_support_ticket(
    ticket_id: int,
    ticket_data: schemas.SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """PERMITE A UN ADMINISTRADOR ACTUALIZAR EL ESTADO O RESPONDER UN TICKET."""
    ticket = SupportService.update_ticket_status(
        db, current_user, ticket_id, ticket_data.estado, ticket_data.respuesta
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    NotificationService.notify_occupancy_change(db)

    messages = SupportService.get_ticket_messages(db, ticket_id)
    return {
        "message": f"Ticket #{ticket_id} actualizado a '{ticket.estado}'",
        "ticket_id": ticket.id,
        "estado": ticket.estado,
        "messages": messages
    }
