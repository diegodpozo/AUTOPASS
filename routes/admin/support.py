from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.support_service import SupportService
from services.notification_service import NotificationService

router = APIRouter()

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

    return {
        "message": f"Ticket #{ticket_id} actualizado a '{ticket.estado}'",
        "ticket_id": ticket.id,
        "estado": ticket.estado
    }
