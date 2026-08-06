from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
import models, schemas
import unicodedata

def normalize_branch_name(text: str) -> str:
    if not text:
        return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class SupportService:

    @staticmethod
    def create_ticket(db: Session, user: models.User, ticket_data: schemas.SupportTicketCreate) -> models.SupportTicket:
        ticket = models.SupportTicket(
            user_id=user.id,
            categoria=ticket_data.categoria,
            sucursal=ticket_data.sucursal or "General",
            asunto=ticket_data.asunto,
            mensaje=ticket_data.mensaje,
            estado="Pendiente"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_user_tickets(db: Session, user_id: int) -> List[models.SupportTicket]:
        return db.query(models.SupportTicket).filter(
            models.SupportTicket.user_id == user_id
        ).order_by(desc(models.SupportTicket.created_at)).all()

    @staticmethod
    def get_admin_tickets(db: Session, current_user: models.User, sucursal_filter: Optional[str] = None, estado_filter: Optional[str] = None) -> List[dict]:
        query = db.query(models.SupportTicket).options(joinedload(models.SupportTicket.user)).order_by(desc(models.SupportTicket.created_at))
        all_tickets = query.all()

        if current_user.rol != "admin":
            # Admin Local o Empleado de una sucursal (ej: Castelar): SOLO ven tickets pertenecientes a su sucursal
            user_suc_norm = normalize_branch_name(current_user.sucursal)
            tickets = [
                t for t in all_tickets
                if user_suc_norm and normalize_branch_name(t.sucursal) == user_suc_norm
            ]
        else:
            # Admin General: por defecto ve las consultas "General". Si aplica filtro especifica o TODAS, se muestra la seleccion.
            if sucursal_filter == "TODAS":
                tickets = all_tickets
            elif sucursal_filter and sucursal_filter not in ["General"]:
                filter_norm = normalize_branch_name(sucursal_filter)
                tickets = [
                    t for t in all_tickets
                    if normalize_branch_name(t.sucursal) == filter_norm
                ]
            else:
                # Consultas generales dirigidas a la red / Admin General
                tickets = [
                    t for t in all_tickets
                    if t.sucursal == "General" or normalize_branch_name(t.sucursal) == "GENERAL" or not t.sucursal
                ]

        if estado_filter and estado_filter != "TODOS":
            tickets = [t for t in tickets if t.estado.upper() == estado_filter.upper()]

        result = []
        for t in tickets:
            result.append({
                "id": t.id,
                "user_id": t.user_id,
                "cliente_nombre": f"{t.user.nombre} {t.user.apellido}".strip() if t.user else "Cliente Eliminado",
                "cliente_email": t.user.email if t.user else "N/A",
                "categoria": t.categoria,
                "sucursal": t.sucursal,
                "asunto": t.asunto,
                "mensaje": t.mensaje,
                "estado": t.estado,
                "respuesta": t.respuesta,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            })

        return result

    @staticmethod
    def update_ticket_status(db: Session, current_user: models.User, ticket_id: int, estado: str, respuesta: Optional[str] = None) -> models.SupportTicket:
        ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
        if not ticket:
            return None

        ticket.estado = estado
        if respuesta:
            ticket.respuesta = respuesta

        db.commit()
        db.refresh(ticket)

        # NOTIFICAR AL USUARIO SOBRE LA RESPUESTA O CAMBIO DE ESTADO DE SU TICKET
        try:
            from services.user_notification_service import UserNotificationService
            titulo_notif = f"Soporte: {ticket.asunto}"
            msg_notif = respuesta if respuesta else f"Tu ticket ha sido actualizado a estado: {estado}."
            UserNotificationService.create_notification(
                db,
                user_id=ticket.user_id,
                tipo="SUPPORT_RESPONSE",
                titulo=titulo_notif,
                mensaje=msg_notif
            )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo crear notificacion de soporte: {e}")

        return ticket
