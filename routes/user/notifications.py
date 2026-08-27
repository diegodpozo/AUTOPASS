from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
import models
import schemas
from services.user_notification_service import UserNotificationService

router = APIRouter(tags=["User Notifications"])

@router.get("/profile/notifications", response_model=schemas.NotificationListResponse)
def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """LISTA LAS NOTIFICACIONES DEL USUARIO LOGUEADO."""
    notifications = UserNotificationService.get_user_notifications(db, current_user.id, limit, offset)
    unread = UserNotificationService.get_unread_count(db, current_user.id)
    total = UserNotificationService.get_total_count(db, current_user.id)
    return schemas.NotificationListResponse(
        notifications=[
            schemas.NotificationResponse.model_validate(n) for n in notifications
        ],
        total=total,
        unread=unread
    )

@router.get("/profile/notifications/unread", response_model=schemas.UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """DEVUELVE LA CANTIDAD DE NOTIFICACIONES NO LEIDAS."""
    count = UserNotificationService.get_unread_count(db, current_user.id)
    return schemas.UnreadCountResponse(count=count)

@router.patch("/profile/notifications/{notif_id}/read", status_code=204)
def mark_as_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """MARCA UNA NOTIFICACION COMO LEIDA."""
    UserNotificationService.mark_as_read(db, notif_id, current_user.id)

@router.post("/profile/notifications/read-all", status_code=204)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """MARCA TODAS LAS NOTIFICACIONES COMO LEIDAS."""
    UserNotificationService.mark_all_as_read(db, current_user.id)

@router.delete("/profile/notifications/clear-read", status_code=204)
def clear_read_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """ELIMINA TODAS LAS NOTIFICACIONES MARCADAS COMO LEIDAS."""
    UserNotificationService.clear_read_notifications(db, current_user.id)

@router.delete("/profile/notifications/{notif_id}", status_code=204)
def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """ELIMINA UNA NOTIFICACION ESPECIFICA."""
    UserNotificationService.delete_notification(db, notif_id, current_user.id)

