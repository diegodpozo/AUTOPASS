from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SupportTicketCreate(BaseModel):
    categoria: str
    sucursal: Optional[str] = "General"
    asunto: str
    mensaje: str

class SupportTicketUpdate(BaseModel):
    estado: str
    respuesta: Optional[str] = None

class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cliente_nombre: Optional[str] = None
    cliente_email: Optional[str] = None
    categoria: str
    sucursal: str
    asunto: str
    mensaje: str
    estado: str
    respuesta: Optional[str] = None
    user_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SupportTicketReply(BaseModel):
    mensaje: str
