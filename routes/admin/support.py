from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.support_service import SupportService
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

@router.patch("/support-tickets/{ticket_id}/read-notifs")
def mark_ticket_notifications_read(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """MARCA COMO LEIDAS LAS NOTIFICACIONES DE UN TICKET PARA EL ADMIN ACTUAL."""
    updated = db.query(models.UserNotification).filter(
        models.UserNotification.ticket_id == ticket_id,
        models.UserNotification.user_id == current_user.id,
        models.UserNotification.leido == False
    ).update({"leido": True})
    db.commit()
    return {"marked": updated}

@router.get("/support-tickets/{ticket_id}")
def get_admin_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_operational_user)
):
    """RETORNA UN TICKET ESPECIFICO CON TODOS SUS MENSAJES."""
    from sqlalchemy.orm import joinedload
    ticket = db.query(models.SupportTicket).options(
        joinedload(models.SupportTicket.user)
    ).filter(models.SupportTicket.id == ticket_id).first()
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

@router.patch("/support-tickets/{ticket_id}")
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
