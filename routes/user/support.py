import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from core.database import get_db
from core.security import get_current_user
from services.support_service import SupportService
from services.notification_service import NotificationService

router = APIRouter()

# EXTENSIONES Y TAMAÑO MAXIMO PERMITIDOS PARA ADJUNTOS (1 MB)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf"}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
UPLOAD_DIR = os.path.join("static", "uploads", "support")

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
            "user_response": t.user_response,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None
        }
        for t in tickets
    ]

@router.get("/support-tickets/{ticket_id}")
def get_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """RETORNA UN TICKET DE SOPORTE ESPECIFICO DEL USUARIO CON TODOS LOS MENSAJES."""
    ticket = SupportService.get_ticket_by_id(db, ticket_id, current_user.id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    messages = SupportService.get_ticket_messages(db, ticket_id)
    return {
        "id": ticket.id,
        "categoria": ticket.categoria,
        "sucursal": ticket.sucursal,
        "asunto": ticket.asunto,
        "mensaje": ticket.mensaje,
        "estado": ticket.estado,
        "respuesta": ticket.respuesta,
        "user_response": ticket.user_response,
        "messages": messages,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
    }

@router.patch("/support-tickets/{ticket_id}/reply")
async def reply_to_support_ticket(
    ticket_id: int,
    mensaje: str = Form(...),
    adjunto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """PERMITE AL USUARIO RESPONDER A UN TICKET DE SOPORTE.
    OPCIONALMENTE PUEDE ADJUNTAR UN ARCHIVO (png/jpg/jpeg/gif/webp/pdf de maximo 1 MB)
    que se guarda en el servidor y se referencia en la BD."""
    adjunto_url = None
    adjunto_nombre = None

    if adjunto and adjunto.filename:
        original_name = adjunto.filename
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Formato no permitido. Adjuntá imágenes (PNG, JPG, GIF, WEBP) o PDF.")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_name = f"support_{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(adjunto.file, buffer)

        size = os.path.getsize(file_path)
        if size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo de 1 MB.")

        adjunto_url = f"/static/uploads/support/{file_name}"
        adjunto_nombre = original_name

    ticket = SupportService.reply_to_ticket(
        db, ticket_id, current_user.id, mensaje,
        adjunto_url=adjunto_url, adjunto_nombre=adjunto_nombre
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    messages = SupportService.get_ticket_messages(db, ticket_id)
    return {
        "message": "Respuesta enviada",
        "ticket_id": ticket.id,
        "estado": ticket.estado,
        "messages": messages
    }
