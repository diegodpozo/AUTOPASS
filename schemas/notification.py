from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    tipo: str
    titulo: str
    mensaje: str
    leido: bool
    reserva_id: Optional[int] = None
    ticket_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread: int

class UnreadCountResponse(BaseModel):
    count: int
