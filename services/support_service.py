from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
import models, schemas
from core.time import localnow
from core.normalize import normalize_branch_name

class SupportService:

    @staticmethod
    def _notify_admins(db: Session, ticket: models.SupportTicket, titulo: str, mensaje: str):
        """NOTIFICA A TODOS LOS ADMINS/LOCAL_ADMINS DE LA SUCURSAL DEL TICKET."""
        try:
            from services.user_notification_service import UserNotificationService
            q = db.query(models.User).filter(
                models.User.rol.in_(["admin", "local_admin"]),
                models.User.is_deleted == False
            )
            if ticket.sucursal and ticket.sucursal != "General":
                user_suc_norm = normalize_branch_name(ticket.sucursal)
                admins = [
                    a for a in q.all()
                    if normalize_branch_name(a.sucursal or "") == user_suc_norm or a.rol == "admin"
                ]
            else:
                admins = [a for a in q.all() if a.rol == "admin"]
            if not admins:
                admins = q.all()
            for admin in admins:
                UserNotificationService.create_notification(
                    db,
                    user_id=admin.id,
                    tipo="SUPPORT_TICKET",
                    titulo=titulo,
                    mensaje=mensaje,
                    ticket_id=ticket.id
                )
        except Exception as e:
            print(f"[ERROR NOTIF] No se pudo notificar a admins de soporte: {e}")

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
        db.flush()

        msg = models.SupportTicketMessage(
            ticket_id=ticket.id,
            user_id=user.id,
            mensaje=ticket_data.mensaje,
            created_at=localnow()
        )
        db.add(msg)
        db.commit()
        db.refresh(ticket)

        suc_text = f" ({ticket.sucursal})" if ticket.sucursal and ticket.sucursal != "General" else ""
        SupportService._notify_admins(
            db, ticket,
            titulo=f"Nuevo ticket{suc_text}: {ticket.asunto}",
            mensaje=f"{user.nombre} {user.apellido} creó un ticket de soporte: {ticket.asunto}"
        )
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
            user_suc_norm = normalize_branch_name(current_user.sucursal)
            tickets = [
                t for t in all_tickets
                if user_suc_norm and normalize_branch_name(t.sucursal) == user_suc_norm
            ]
        else:
            if sucursal_filter == "TODAS":
                tickets = all_tickets
            elif sucursal_filter and sucursal_filter not in ["General"]:
                filter_norm = normalize_branch_name(sucursal_filter)
                tickets = [
                    t for t in all_tickets
                    if normalize_branch_name(t.sucursal) == filter_norm
                ]
            else:
                tickets = [
                    t for t in all_tickets
                    if t.sucursal == "General" or normalize_branch_name(t.sucursal) == "GENERAL" or not t.sucursal
                ]

        if estado_filter and estado_filter != "TODOS":
            tickets = [t for t in tickets if t.estado.upper() == estado_filter.upper()]

        # Auto-limpiar notificaciones pendientes de tickets que ya fueron resueltos o cancelados
        resolved_ticket_ids = [t.id for t in tickets if t.estado.lower() in ("resuelto", "cancelado")]
        if resolved_ticket_ids:
            db.query(models.UserNotification).filter(
                models.UserNotification.ticket_id.in_(resolved_ticket_ids),
                models.UserNotification.leido == False
            ).update({"leido": True}, synchronize_session=False)
            db.commit()

        # Obtener los ticket_id que tienen notificaciones sin leer para el usuario actual
        unread_ticket_ids = set(
            r[0] for r in db.query(models.UserNotification.ticket_id).filter(
                models.UserNotification.user_id == current_user.id,
                models.UserNotification.ticket_id.isnot(None),
                models.UserNotification.leido == False
            ).all()
        )

        result = []
        for t in tickets:
            messages = db.query(models.SupportTicketMessage).filter(
                models.SupportTicketMessage.ticket_id == t.id
            ).order_by(models.SupportTicketMessage.created_at).all()
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
                "has_unread": t.id in unread_ticket_ids,
                "messages": [
                    {
                        "id": m.id,
                        "user_id": m.user_id,
                        "mensaje": m.mensaje,
                        "is_admin": m.user.rol in ("admin", "local_admin") if m.user else False,
                        "autor": f"{m.user.nombre} {m.user.apellido}" if m.user else "Desconocido",
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ],
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

        if respuesta:
            msg = models.SupportTicketMessage(
                ticket_id=ticket.id,
                user_id=current_user.id,
                mensaje=respuesta,
                created_at=localnow()
            )
            db.add(msg)

        # Marcar todas las notificaciones asociadas a este ticket como leídas
        db.query(models.UserNotification).filter(
            models.UserNotification.ticket_id == ticket_id,
            models.UserNotification.leido == False
        ).update({"leido": True})

        db.commit()
        db.refresh(ticket)

        if respuesta:
            admin_name = f"{current_user.nombre} {current_user.apellido}"
            try:
                from services.user_notification_service import UserNotificationService
                UserNotificationService.create_notification(
                    db,
                    user_id=ticket.user_id,
                    tipo="SUPPORT_RESPONSE",
                    titulo=f"Soporte: {ticket.asunto}",
                    mensaje=f"{admin_name} respondió: {respuesta[:100]}",
                    ticket_id=ticket.id
                )
            except Exception as e:
                print(f"[ERROR NOTIF] No se pudo crear notificacion de soporte: {e}")

        return ticket

    @staticmethod
    def get_ticket_by_id(db: Session, ticket_id: int, user_id: int) -> Optional[models.SupportTicket]:
        return db.query(models.SupportTicket).filter(
            models.SupportTicket.id == ticket_id,
            models.SupportTicket.user_id == user_id
        ).first()

    @staticmethod
    def get_ticket_messages(db: Session, ticket_id: int) -> List[dict]:
        messages = db.query(models.SupportTicketMessage).filter(
            models.SupportTicketMessage.ticket_id == ticket_id
        ).order_by(models.SupportTicketMessage.created_at).all()
        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "mensaje": m.mensaje,
                "is_admin": m.user.rol in ("admin", "local_admin") if m.user else False,
                "autor": f"{m.user.nombre} {m.user.apellido}" if m.user else "Desconocido",
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]

    @staticmethod
    def reply_to_ticket(db: Session, ticket_id: int, user_id: int, mensaje: str) -> Optional[models.SupportTicket]:
        ticket = db.query(models.SupportTicket).filter(
            models.SupportTicket.id == ticket_id,
            models.SupportTicket.user_id == user_id
        ).first()
        if not ticket:
            return None

        msg = models.SupportTicketMessage(
            ticket_id=ticket.id,
            user_id=user_id,
            mensaje=mensaje,
            created_at=localnow()
        )
        db.add(msg)
        ticket.user_response = mensaje
        ticket.estado = "En revisión"
        db.commit()
        db.refresh(ticket)

        SupportService._notify_admins(
            db, ticket,
            titulo=f"Respuesta de cliente: {ticket.asunto}",
            mensaje=f"El cliente respondió en ticket #{ticket.id}: {mensaje[:100]}"
        )
        return ticket

    @staticmethod
    def get_admin_pending_count(db: Session, current_user) -> int:
        """CUENTA LOS TICKETS DE SOPORTE PENDIENTES (NO RESUELTOS) QUE PUEDE VER
        EL ADMINISTRADOR ACTUAL, SEGUN SU ROL Y SUCURSAL. Este contador alimenta
        la burbuja de 'Soporte & Tickets' del menu lateral (no las notificaciones)."""
        all_tickets = db.query(models.SupportTicket).all()

        if current_user.rol != "admin":
            user_suc_norm = normalize_branch_name(current_user.sucursal or "")
            scoped = [
                t for t in all_tickets
                if user_suc_norm and normalize_branch_name(t.sucursal or "") == user_suc_norm
            ]
        else:
            # El super admin por defecto ve los tickets generales o sin sucursal (misma regla que get_admin_tickets)
            scoped = [
                t for t in all_tickets
                if t.sucursal == "General"
                or normalize_branch_name(t.sucursal or "") == "GENERAL"
                or not t.sucursal
            ]

        return len([
            t for t in scoped
            if (t.estado or "").strip().lower() not in ("resuelto", "resuelta")
        ])
