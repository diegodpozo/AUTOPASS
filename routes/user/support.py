from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_current_user
from services.support_service import SupportService
from services.notification_service import NotificationService

router = APIRouter()

@router.post("/support-tickets", status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    ticket_data: schemas.SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """PERMITE A UN CLIENTE CREAR UN TICKET DE SOPORTE."""
    ticket = SupportService.create_ticket(db, current_user, ticket_data)
    NotificationService.notify_occupancy_change(db)
    return {
        "message": "Ticket creado exitosamente",
        "ticket_id": ticket.id,
        "sucursal": ticket.sucursal,
        "estado": ticket.estado
    }

@router.get("/support-tickets")
def get_my_support_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """RETORNA LOS TICKETS DE SOPORTE DEL USUARIO AUTENTICADO."""
    tickets = SupportService.get_user_tickets(db, current_user.id)
    return [
        {
            "id": t.id,
            "categoria": t.categoria,
            "sucursal": t.sucursal,
            "asunto": t.asunto,
            "mensaje": t.mensaje,
            "estado": t.estado,
            "respuesta": t.respuesta,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None
        }
        for t in tickets
    ]
